# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-08-15 22:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0005_repository_release_tag_regex'),
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='release',
            unique_together=set([('repo', 'git_tag')]),
        ),
    ]
