# Generated by Django 5.1.7 on 2025-07-12 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0016_dispatchhistory_dispatchitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnitem',
            name='branch',
            field=models.CharField(choices=[('Сокулук', 'Сокулук'), ('Беловодское', 'Беловодское')], default=0, max_length=100, verbose_name='Филиал'),
            preserve_default=False,
        ),
    ]
