from django.db import migrations


def create_groups(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.get_or_create(name="Managers")
    group.objects.get_or_create(name="Installers")


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0003_order_created_by_order_deleted_at_order_deleted_by_and_more"),
    ]

    operations = [
        migrations.RunPython(create_groups, migrations.RunPython.noop),
    ]
