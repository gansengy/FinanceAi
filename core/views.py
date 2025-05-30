import traceback
from collections import defaultdict
from django.shortcuts import render
from .forms import CheckUploadForm
from .models import Transaction
from .utils.gpt import parse_receipt_image
from .utils.llama_utils import safe_parse_llama_json
import tempfile
from django.db.models import Sum
from django.utils.timezone import now

def transaction_list(request):
    transactions = Transaction.objects.order_by('-created_at')
    return render(request, 'core/transaction_list.html', {'transactions': transactions})

def dashboard(request):
    transactions = Transaction.objects.all()
    now_date = now()

    month_sum = transactions.filter(created_at__month=now_date.month).aggregate(Sum('price'))['price__sum'] or 0
    week_sum = transactions.filter(created_at__week=now_date.isocalendar()[1]).aggregate(Sum('price'))['price__sum'] or 0
    last_transactions = transactions.order_by('-created_at')[:5]

    # Группировка по категориям
    from django.db.models import Count
    category_data = (
        transactions.values('category')
        .annotate(total=Sum('price'), count=Count('id'))
        .order_by('-total')
    )

    return render(request, 'core/dashboard.html', {
        'month_sum': month_sum,
        'week_sum': week_sum,
        'last_transactions': last_transactions,
        'category_data': category_data,
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
                        cat = item.get("category", "інше").strip().lower()
                        grouped_items[cat].append(item)

                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        Transaction.objects.create(
                            name=item.get("name", "невідомо"),
                            price=float(item.get("price", 0)),
                            category=item.get("category", "інше").strip().lower()
                        )

                result_text = "[GPT-4o] Чек оброблено нейромережею напряму з картинки."

            except Exception as e:
                print("⛔ GPT-4o IMAGE PARSE ERROR:")
                traceback.print_exc()

    else:
        form = CheckUploadForm()

    return render(request, 'core/upload.html', {
        'form': form,
        'result_text': result_text,
        'parsed_items': parsed_items,
        'grouped_items': dict(grouped_items),
    })
