# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-11 21:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_planbranchnotification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planbranchnotification',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='planbranchnotification',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='planbranchnotification',
            name='user',
        ),
        migrations.DeleteModel(
            name='PlanBranchNotification',
        ),
    ]
