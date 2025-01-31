# Generated by Django 5.1.2 on 2024-11-05 02:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('price', models.SmallIntegerField()),
                ('event_date', models.DateField()),
                ('content', models.TextField()),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='author', to='accounts.profile')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorys', to='events.category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(max_length=30)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seats', to='events.event')),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='events', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_user', to='accounts.profile')),
                ('tickets', models.ManyToManyField(related_name='reservations', to='events.seat')),
            ],
        ),
    ]
