# Generated by Django 5.1.7 on 2025-06-17 06:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_alter_stock_fixed_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnitem',
            name='sale_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_records', to='clients.saleitem'),
        ),
    ]
