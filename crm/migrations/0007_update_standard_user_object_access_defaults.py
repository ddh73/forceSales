from django.db import migrations


def update_standard_user_object_access_defaults(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    profile_permission_model = apps.get_model("crm", "ProfileObjectPermission")

    standard_group, _ = group_model.objects.get_or_create(name="Standard User")
    standard_profile_defaults = {
        "account": {
            "can_read": True,
            "can_write": True,
            "can_read_all": True,
            "can_edit_all": True,
        },
        "opportunity": {
            "can_read": True,
            "can_write": True,
            "can_read_all": False,
            "can_edit_all": False,
        },
    }

    for model_name, defaults in standard_profile_defaults.items():
        content_type, _ = content_type_model.objects.get_or_create(app_label="crm", model=model_name)
        profile_permission_model.objects.update_or_create(
            profile=standard_group,
            content_type=content_type,
            defaults=defaults,
        )


def restore_previous_standard_user_object_access_defaults(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    profile_permission_model = apps.get_model("crm", "ProfileObjectPermission")

    standard_group = group_model.objects.filter(name="Standard User").first()
    if not standard_group:
        return

    account_content_type, _ = content_type_model.objects.get_or_create(app_label="crm", model="account")
    profile_permission_model.objects.update_or_create(
        profile=standard_group,
        content_type=account_content_type,
        defaults={
            "can_read": True,
            "can_write": True,
            "can_read_all": False,
            "can_edit_all": False,
        },
    )
    opportunity_content_type = content_type_model.objects.filter(app_label="crm", model="opportunity").first()
    if opportunity_content_type:
        profile_permission_model.objects.filter(
            profile=standard_group,
            content_type=opportunity_content_type,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0006_account_owner_opportunity_owner_and_more"),
    ]

    operations = [
        migrations.RunPython(
            update_standard_user_object_access_defaults,
            restore_previous_standard_user_object_access_defaults,
        ),
    ]
