import base64

import openai
import os
import openai
from openai import OpenAI


client = OpenAI(api_key = "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")
def parse_receipt_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "На зображенні — чек. Витягни всі товари, їх назви, ціни та категорії.\n"
                            "Поверни ВИКЛЮЧНО валідний JSON масив у форматі:\n"
                            "[{\"name\": \"Назва товару\", \"price\": 00.00, \"category\": \"Назва категорії\"}]\n\n"
                            "🔹 Товари можуть бути українською або англійською. Якщо бачиш англійське слово — переклади на українську.\n"
                            "🔹 Ціна — тільки число з крапкою. Якщо ціна некоректна — не включай товар.\n"
                            "🔹 Вибирай категорію лише з цього списку:\n"
                            "- \"їжа\"\n"
                            "- \"напої\"\n"
                            "- \"алкоголь\"\n"
                            "- \"одяг\"\n"
                            "- \"побут\"\n"
                            "- \"медицина\"\n"
                            "- \"техніка\"\n"
                            "- \"транспорт\"\n"
                            "- \"розваги\"\n"
                            "- \"інше\"\n"
                            "🔹 Якщо не впевнений — став категорію \"інше\".\n"
                            "🔹 НЕ пиши нічого крім JSON. Без пояснень. Без тексту. Без прикладів."
                        ),

                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "auto"
                        },
                    }
                ],
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )

    return response.choices[0].message.content.strip()
