# Generated by Django 4.0.4 on 2022-05-24 07:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('servicecentres', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicecenters',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='servicecentres.serviceregions', verbose_name='Регион'),
        ),
    ]