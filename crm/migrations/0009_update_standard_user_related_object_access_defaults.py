from django.db import migrations


STANDARD_PROFILE_DEFAULTS = {
    "opportunitylineitem": {
        "can_read": True,
        "can_write": True,
        "can_read_all": False,
        "can_edit_all": False,
    },
    "product": {
        "can_read": True,
        "can_write": False,
        "can_read_all": False,
        "can_edit_all": False,
    },
}


def update_standard_user_related_object_access_defaults(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    profile_permission_model = apps.get_model("crm", "ProfileObjectPermission")

    standard_group, _ = group_model.objects.get_or_create(name="Standard User")
    for model_name, defaults in STANDARD_PROFILE_DEFAULTS.items():
        content_type, _ = content_type_model.objects.get_or_create(app_label="crm", model=model_name)
        profile_permission_model.objects.update_or_create(
            profile=standard_group,
            content_type=content_type,
            defaults=defaults,
        )


def remove_standard_user_related_object_access_defaults(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    profile_permission_model = apps.get_model("crm", "ProfileObjectPermission")

    standard_group = group_model.objects.filter(name="Standard User").first()
    if not standard_group:
        return

    content_types = content_type_model.objects.filter(
        app_label="crm",
        model__in=STANDARD_PROFILE_DEFAULTS.keys(),
    )
    profile_permission_model.objects.filter(
        profile=standard_group,
        content_type__in=content_types,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0008_alter_opportunity_options"),
    ]

    operations = [
        migrations.RunPython(
            update_standard_user_related_object_access_defaults,
            remove_standard_user_related_object_access_defaults,
        ),
    ]
