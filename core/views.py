import traceback
import json
from django.db import models
from collections import defaultdict
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import CheckUploadForm, TransactionForm, CategoryForm, IncomeForm
from .models import Transaction, Category
from .utils.gpt import parse_receipt_image
from .utils.llama_utils import safe_parse_llama_json
import tempfile
from django.db.models import Sum, Count
from django.utils.timezone import now
from django.db.models import Q


def transaction_list(request):
    search_query = request.GET.get('search', '')  # Отримання параметра пошуку
    if search_query:
        transactions = Transaction.objects.filter(Q(name__icontains=search_query))
    else:
        transactions = Transaction.objects.all()
    return render(request, 'core/transaction_list.html', {'transactions': transactions, 'search_query': search_query})


def edit_transaction(request, transaction_id):
    """Редагування транзакції"""
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Визначаємо тип форми залежно від типу транзакції
    if transaction.transaction_type == 'income':
        form_class = IncomeForm
    else:
        form_class = TransactionForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Транзакцію успішно оновлено!')
            return redirect('transaction_list')
    else:
        form = form_class(instance=transaction)

    return render(request, 'core/edit_transaction.html', {
        'form': form,
        'transaction': transaction
    })


def delete_transaction(request, transaction_id):
    """Видалення транзакції"""
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.method == 'POST':
        transaction_name = transaction.name
        transaction.delete()
        messages.success(request, f'Транзакцію "{transaction_name}" успішно видалено!')
        return redirect('transaction_list')

    return render(request, 'core/delete_transaction.html', {
        'transaction': transaction
    })


def dashboard(request):
    transactions = Transaction.objects.all()
    now_date = now()

    # Розділяємо витрати та прибутки
    expenses = transactions.filter(transaction_type='expense')
    incomes = transactions.filter(transaction_type='income')

    # Calculate week and month sums для витрат
    month_expenses = expenses.filter(
        created_at__year=now_date.year,
        created_at__month=now_date.month
    ).aggregate(total=Sum('price'))['total'] or 0

    current_week = now_date.isocalendar()[1]
    week_expenses = expenses.filter(
        created_at__year=now_date.year,
        created_at__week=current_week
    ).aggregate(total=Sum('price'))['total'] or 0

    # Calculate week and month sums для прибутків
    month_income = incomes.filter(
        created_at__year=now_date.year,
        created_at__month=now_date.month
    ).aggregate(total=Sum('price'))['total'] or 0

    week_income = incomes.filter(
        created_at__year=now_date.year,
        created_at__week=current_week
    ).aggregate(total=Sum('price'))['total'] or 0

    # Баланс
    month_balance = month_income - month_expenses
    week_balance = week_income - week_expenses

    # Get last 5 transactions
    last_transactions = transactions.order_by('-created_at')[:5]

    # Category data for pie chart - тільки витрати
    category_data = (
        expenses.values('category__name', 'category__icon')
        .annotate(total=Sum('price'), count=Count('id'))
        .order_by('-total')
    )

    # Prepare data for charts
    category_labels = []
    category_amounts = []
    for cat in category_data:
        if cat['category__name']:
            label = f"{cat['category__icon']} {cat['category__name'].title()}"
        else:
            label = 'Без категорії'
        category_labels.append(label)
        category_amounts.append(float(cat['total']))

    # Monthly data for line chart (last 30 days) - витрати та прибутки
    monthly_labels = []
    monthly_expenses_data = []
    monthly_income_data = []

    end_date = now_date.date()
    start_date = end_date - timedelta(days=30)

    current_date = start_date
    while current_date <= end_date:
        daily_expenses = expenses.filter(
            created_at__date=current_date
        ).aggregate(total=Sum('price'))['total'] or 0

        daily_income = incomes.filter(
            created_at__date=current_date
        ).aggregate(total=Sum('price'))['total'] or 0

        monthly_labels.append(current_date.strftime('%d.%m'))
        monthly_expenses_data.append(float(daily_expenses))
        monthly_income_data.append(float(daily_income))
        current_date += timedelta(days=1)

    return render(request, 'core/dashboard.html', {
        'month_expenses': month_expenses,
        'week_expenses': week_expenses,
        'month_income': month_income,
        'week_income': week_income,
        'month_balance': month_balance,
        'week_balance': week_balance,
        'last_transactions': last_transactions,
        'category_data': category_data,
        'category_labels': json.dumps(category_labels),
        'category_amounts': json.dumps(category_amounts),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_expenses_data': json.dumps(monthly_expenses_data),
        'monthly_income_data': json.dumps(monthly_income_data),
    })

def upload_check(request):
    result_text = None
    parsed_items = None
    grouped_items = defaultdict(list)

    if request.method == 'POST':
        form = CheckUploadForm(request.POST, request.FILES)

        if form.is_valid():
            image_file = form.cleaned_data['image']

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(image_file.read())
                    tmp_path = tmp.name

                print(f"📂 Збережено тимчасовий файл: {tmp_path}")

                gpt_response = parse_receipt_image(tmp_path)
                parsed_items = safe_parse_llama_json(gpt_response)

                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        cat_name = item.get("category", "інше").strip().lower()
                        grouped_items[cat_name].append(item)

                # Save transactions to database with new Category model
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        # Знайти або створити категорію
                        category_name = item.get("category", "інше").strip().lower()

                        # Спробувати знайти існуючу категорію
                        try:
                            category = Category.objects.get(name=category_name)
                        except Category.DoesNotExist:
                            # Якщо категорії немає, використати "інше"
                            category = Category.objects.get(name="інше")

                        Transaction.objects.create(
                            name=item.get("name", "невідомо"),
                            price=float(item.get("price", 0)),
                            category=category
                        )

                result_text = "[GPT-4o] Чек оброблено нейромережею напряму з картинки."
                messages.success(request, f"Успішно додано {len(parsed_items)} товарів!")

            except Exception as e:
                print("⛔ GPT-4o IMAGE PARSE ERROR:")
                print(f"Error: {str(e)}")
                traceback.print_exc()
                result_text = f"Помилка при обробці чеку: {str(e)}"
                messages.error(request, "Помилка при обробці чеку")

    else:
        form = CheckUploadForm()

    return render(request, 'core/upload.html', {
        'form': form,
        'result_text': result_text,
        'parsed_items': parsed_items,
        'grouped_items': dict(grouped_items),
    })


def manual_transaction(request):
    """Ручне додавання транзакції та прибутків"""
    expense_form = None
    income_form = None

    if request.method == 'POST':
        # Перевіряємо, яка форма була надіслана
        if 'expense_submit' in request.POST:
            expense_form = TransactionForm(request.POST)
            if expense_form.is_valid():
                transaction = expense_form.save(commit=False)
                transaction.transaction_type = 'expense'
                transaction.save()
                messages.success(request, f'Витрату "{transaction.name}" успішно додано!')
                expense_form = TransactionForm()  # Очистити форму

        elif 'income_submit' in request.POST:
            income_form = IncomeForm(request.POST)
            if income_form.is_valid():
                transaction = income_form.save()
                messages.success(request, f'Прибуток "{transaction.name}" успішно додано!')
                income_form = IncomeForm()  # Очистити форму

    # Ініціалізуємо форми, якщо вони ще не створені
    if expense_form is None:
        expense_form = TransactionForm()
    if income_form is None:
        income_form = IncomeForm()

    # Отримати останні 10 транзакцій (витрати та прибутки)
    last_transactions = Transaction.objects.all()[:10]

    return render(request, 'core/transaction_manual.html', {
        'expense_form': expense_form,
        'income_form': income_form,
        'last_transactions': last_transactions
    })


def category_list(request):
    """Список категорій"""
    categories = Category.objects.all()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію успішно додано!')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'core/category_list.html', {
        'categories': categories,
        'form': form
    })


def edit_category(request, category_id):
    """Редагування категорії"""
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію успішно оновлено!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'core/edit_category.html', {
        'form': form,
        'category': category
    })


def delete_category(request, category_id):
    """Видалення категорії"""
    category = get_object_or_404(Category, id=category_id)

    # Перевірка, чи це базова категорія
    if category.is_default:
        messages.error(request, "Не можна видалити базову категорію!")
        return redirect('category_list')

    if request.method == 'POST':
        category_name = category.name
        try:
            category.delete()
            messages.success(request, f'Категорію "{category_name}" успішно видалено!')
        except models.ProtectedError:
            messages.error(request, "Не можна видалити цю категорію!")
        return redirect('category_list')

    # Підрахувати кількість транзакцій в цій категорії
    transaction_count = Transaction.objects.filter(category=category).count()

    return render(request, 'core/delete_category.html', {
        'category': category,
        'transaction_count': transaction_count
    })


def user_profile(request):
    """Профіль користувача"""
    if request.method == 'POST':
        # Тимчасово просто показуємо повідомлення
        messages.info(request, 'Функція редагування профілю ще в розробці')
        return redirect('user_profile')

    # Тимчасові дані для відображення
    context = {
        'user_data': {
            'first_name': 'Іван',
            'last_name': 'Петренко',
            'email': 'ivan.petrenko@email.com',
            'birth_date': '1990-05-15',
            'total_transactions': Transaction.objects.count(),
            'month_expenses': Transaction.objects.filter(
                transaction_type='expense',
                created_at__month=now().month,
                created_at__year=now().year
            ).aggregate(total=Sum('price'))['total'] or 0,
            'month_income': Transaction.objects.filter(
                transaction_type='income',
                created_at__month=now().month,
                created_at__year=now().year
            ).aggregate(total=Sum('price'))['total'] or 0,
        }
    }

    return render(request, 'core/user_profile.html', context)