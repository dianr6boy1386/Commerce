from django.db import migrations


def seed_categories(apps, schema_editor):
    Category = apps.get_model("auctions", "Category")
    for name in [
        "Electronics",
        "Fashion",
        "Home",
        "Books",
        "Collectibles",
        "Sports",
        "Other",
    ]:
        Category.objects.get_or_create(name=name)


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("auctions", "Category")
    Category.objects.filter(
        name__in=[
            "Electronics",
            "Fashion",
            "Home",
            "Books",
            "Collectibles",
            "Sports",
            "Other",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auctions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
