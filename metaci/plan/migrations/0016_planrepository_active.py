# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-20 21:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0015_auto_20180314_2252'),
    ]

    operations = [
        migrations.AddField(
            model_name='planrepository',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
