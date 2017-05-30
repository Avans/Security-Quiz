# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0003_auto_20150520_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='LetsEncryptChallenge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('challenge', models.CharField(max_length=128)),
                ('response', models.CharField(max_length=128)),
                ('expiry_date', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
