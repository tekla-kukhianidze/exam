# shop/migrations/0004_create_initial_categories.py

from django.db import migrations


def create_initial_categories(apps, schema_editor):
    Category = apps.get_model('shop', 'Category')

    categories_to_create = [
        ("სკამი", "chair", "კომფორტული და თანამედროვე სკამები."),
        ("დივანი", "sofa", "სხვადასხვა ზომისა და მასალის დივნები."),
        ("მაგიდა", "table", "სასადილო, საოფისე და ყავის მაგიდები."),
        ("კარადა", "wardrobe", "ტანსაცმლის და შესანახი კარადები."),
        ("საწოლი", "bed", "ორადგილიანი და ერთადგილიანი საწოლები."),
        ("ტუმბო", "nightstand", "პატარა ტუმბოები და კომოდები."),
        ("თარო", "shelf", "კედლის და იატაკის თაროები."),
        ("სავარძელი", "armchair", "დასასვენებელი და დეკორატიული სავარძლები."),
        ("ეზოს ავეჯი", "outdoor-furniture", "აივნისა და ეზოს ავეჯის კოლექცია."),
    ]

    for name_ge, slug_en, description in categories_to_create:
        # შეამოწმეთ, რომ კატეგორია არ არსებობს, სანამ შექმნით (დუბლირების თავიდან ასაცილებლად)
        if not Category.objects.filter(slug=slug_en).exists():
            Category.objects.create(
                name=name_ge,
                slug=slug_en,
                description=description,
                is_active=True
            )


class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0003_alter_order_order_number'),  # <-- ეს უნდა იყოს ბოლო მიგრაციის სახელი თქვენს სიაში
    ]

    operations = [
        migrations.RunPython(create_initial_categories),
    ]