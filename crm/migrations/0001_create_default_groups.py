from django.db import migrations


def create_default_groups(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    permission = apps.get_model("auth", "Permission")

    admin_group, _ = group.objects.get_or_create(name="CRM Admin")
    standard_group, _ = group.objects.get_or_create(name="Standard User")

    user_permissions = permission.objects.filter(
        content_type__app_label="auth",
        codename__in={"add_user", "change_user", "view_user"},
    )
    admin_group.permissions.add(*user_permissions)

    # Standard users intentionally receive no Django admin permissions yet. The
    # application dashboard remains available to every authenticated user.
    standard_group.permissions.clear()


def remove_default_groups(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.filter(name__in=["CRM Admin", "Standard User"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_default_groups, remove_default_groups),
    ]
