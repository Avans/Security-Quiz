# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='submitted',
            field=models.DateField(auto_now_add=True, null=True),
            preserve_default=True,
        ),
    ]
