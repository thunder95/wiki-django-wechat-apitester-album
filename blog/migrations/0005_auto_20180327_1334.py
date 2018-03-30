# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-03-27 13:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_media_album_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='media_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Media'),
        ),
        migrations.AlterField(
            model_name='youzipic',
            name='pic_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Media'),
        ),
    ]
