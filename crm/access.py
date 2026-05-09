from dataclasses import dataclass

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType

from .models import ProfileObjectPermission


@dataclass(frozen=True)
class ObjectAccess:
    can_read: bool = False
    can_write: bool = False
    can_read_all: bool = False
    can_edit_all: bool = False

    @property
    def can_create(self):
        return self.can_write or self.can_edit_all

    @property
    def can_read_records(self):
        return self.can_read or self.can_read_all or self.can_edit_all

    @property
    def can_edit_records(self):
        return self.can_write or self.can_edit_all


def get_object_access(user, model):
    """Return the combined object access for a user and model."""
    if not user.is_authenticated:
        return ObjectAccess()
    if user.is_superuser or user.groups.filter(name="CRM Admin").exists():
        return ObjectAccess(can_read=True, can_write=True, can_read_all=True, can_edit_all=True)

    content_type = ContentType.objects.get_for_model(model)
    profiles = list(user.groups.all())
    standard_profile = Group.objects.filter(name="Standard User").first()
    if standard_profile and standard_profile not in profiles:
        profiles.append(standard_profile)

    permissions = ProfileObjectPermission.objects.filter(profile__in=profiles, content_type=content_type)
    return ObjectAccess(
        can_read=permissions.filter(can_read=True).exists(),
        can_write=permissions.filter(can_write=True).exists(),
        can_read_all=permissions.filter(can_read_all=True).exists(),
        can_edit_all=permissions.filter(can_edit_all=True).exists(),
    )


def scope_queryset_to_readable_records(queryset, user):
    """Limit a queryset to records the user may read."""
    access = get_object_access(user, queryset.model)
    if access.can_read_all or access.can_edit_all:
        return queryset
    if access.can_read and hasattr(queryset.model, "owner_id"):
        return queryset.filter(owner=user)
    return queryset.none()


def user_can_read_record(user, record):
    access = get_object_access(user, record.__class__)
    if access.can_read_all or access.can_edit_all:
        return True
    return access.can_read and getattr(record, "owner_id", None) == user.pk


def user_can_edit_record(user, record):
    access = get_object_access(user, record.__class__)
    if access.can_edit_all:
        return True
    return access.can_write and getattr(record, "owner_id", None) == user.pk
