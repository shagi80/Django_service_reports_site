# Generated by Django 4.0.4 on 2022-05-31 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_alter_mainproducts_options_codes_baseprice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseprice',
            name='repair_type',
            field=models.CharField(choices=[('none', 'нуказывается'), ('document', 'выписка документов'), ('easy', 'простой'), ('middle', 'средний'), ('difficult', 'сложный')], max_length=50, verbose_name='Вид ремонта'),
        ),
        migrations.AlterField(
            model_name='codes',
            name='is_folder',
            field=models.BooleanField(blank=True, verbose_name='Это группа'),
        ),
        migrations.AlterField(
            model_name='codes',
            name='parent',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_folder': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent_code', to='products.codes', verbose_name='Группа'),
        ),
        migrations.AlterField(
            model_name='codes',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='code_product', to='products.mainproducts', verbose_name='Вид продукции'),
        ),
        migrations.AlterField(
            model_name='codes',
            name='repair_type',
            field=models.CharField(choices=[('none', 'нуказывается'), ('document', 'выписка документов'), ('easy', 'простой'), ('middle', 'средний'), ('difficult', 'сложный')], max_length=50, verbose_name='Вид ремонта'),
        ),
    ]
