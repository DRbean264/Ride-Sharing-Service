# Generated by Django 4.0.1 on 2022-01-12 06:40

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RideShareServiceUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstName', models.CharField(max_length=100, verbose_name='First Name')),
                ('middleName', models.CharField(blank=True, max_length=100, verbose_name='Middle Name')),
                ('lastName', models.CharField(max_length=100, verbose_name='Last Name')),
                ('phoneNumber', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True, verbose_name='Phone Number')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('birthday', models.DateField(verbose_name='Date of birth')),
                ('gender', models.IntegerField(choices=[(0, 'female'), (1, 'male'), (2, 'prefer not to tell')], verbose_name='Gender')),
            ],
        ),
    ]
