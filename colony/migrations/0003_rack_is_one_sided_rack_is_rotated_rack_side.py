# Generated by Django 5.1 on 2024-09-11 02:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0002_cage_position_rack_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='is_one_sided',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rack',
            name='is_rotated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rack',
            name='side',
            field=models.CharField(choices=[('L', 'Left'), ('R', 'Right')], default='L', max_length=1),
            preserve_default=False,
        ),
    ]
