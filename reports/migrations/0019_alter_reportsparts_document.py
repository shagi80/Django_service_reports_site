# Generated by Django 4.0.4 on 2023-03-03 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_reportsparts_order_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportsparts',
            name='document',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Реквизиты накладной'),
        ),
    ]
