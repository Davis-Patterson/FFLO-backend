# Generated by Django 5.1.1 on 2024-11-13 04:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Server', '0008_bookrental_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('message', models.TextField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterField(
            model_name='book',
            name='language',
            field=models.CharField(default='Français', max_length=20),
        ),
    ]
