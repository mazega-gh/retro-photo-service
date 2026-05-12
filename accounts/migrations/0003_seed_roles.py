from django.db import migrations


ROLE_NAMES = ('user', 'moderator', 'admin')


def seed_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    for name in ROLE_NAMES:
        Role.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_email'),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
