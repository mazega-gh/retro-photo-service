from django.db import migrations, models


STATUS_NAMES = ('На проверке', 'Опубликовано', 'Отклонено')


def seed_statuses(apps, schema_editor):
    ModerationStatus = apps.get_model('moderation', 'ModerationStatus')
    for name in STATUS_NAMES:
        ModerationStatus.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0003_alter_moderationlog_moderator'),
    ]

    operations = [
        migrations.AddField(
            model_name='moderationlog',
            name='action',
            field=models.CharField(blank=True, max_length=32, verbose_name='Action'),
        ),
        migrations.RunPython(seed_statuses, migrations.RunPython.noop),
    ]
