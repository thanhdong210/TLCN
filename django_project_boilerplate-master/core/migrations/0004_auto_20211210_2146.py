# Generated by Django 2.2 on 2021-12-10 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(choices=[('R', 'Rau'), ('C', 'Cu')], max_length=2),
        ),
    ]
