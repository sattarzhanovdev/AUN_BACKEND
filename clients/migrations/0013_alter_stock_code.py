# Generated by Django 5.1.7 on 2025-07-08 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0012_alter_stock_fixed_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='code',
            field=models.CharField(max_length=50),
        ),
    ]
