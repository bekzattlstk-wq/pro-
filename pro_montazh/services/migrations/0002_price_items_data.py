from decimal import Decimal

from django.db import migrations

PRICE_ITEMS = [
    ("Установка дверей стоимостью эконом класса до 2000р", "2000.00"),
    ("Установка двери МДФ", "1800.00"),
    ("Установка деревянных дверей", "1800.00"),
    ("Двери эмаль, телескоп и стоимостью от 8000р", "2500.00"),
    ("Установка двери (от 2-х шт) телескоп стоимостью от 2000руб.", "2200.00"),
    ("Установка одной двери на объекте (минимальный выезд)", "3600.00"),
    ("Установка распашной двустворчатой двери", "4000.00"),
    ("Установка распашной двустворчатой двери телескоп, эмаль и стоимостью от 8000руб.", "4500.00"),
    ('Установка двери "книжка"', "4000.00"),
    ('Установка двустворчатой двери "книжка"', "8000.00"),
    ("Установка шпонированной двери", "2200.00"),
    ('Установка двери с Компланарной коробкой (от 2-х шт) "Silvia" на клей', "3500.00"),
    ("Установка дверей экошпон", "2200.00"),
    ("Установка дверей книжка", "3000.00"),
    ("Установка стеклянных дверей", "2500.00"),
    ("Установка двери из массива ценных пород дерева (бук, дуб и т. д.)", "3500.00"),
    ("Установка откатных дверей", "2500.00"),
    ("Установка дверей гармошка", "1800.00"),
]


def create_price_items(apps, schema_editor):
    PriceItem = apps.get_model('services', 'PriceItem')
    for position, (title, price) in enumerate(PRICE_ITEMS, start=1):
        PriceItem.objects.get_or_create(
            title=title,
            defaults={'price': Decimal(price), 'position': position},
        )


def remove_price_items(apps, schema_editor):
    PriceItem = apps.get_model('services', 'PriceItem')
    PriceItem.objects.filter(title__in=[title for title, _ in PRICE_ITEMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_price_items, remove_price_items),
    ]
