# Generated by Django 5.0.6 on 2024-05-20 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_api', '0006_availableseat'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestView',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'test_view',
                'managed': False,
            },
        ),
    ]
