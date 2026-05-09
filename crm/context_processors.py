import re

from django.conf import settings
from django.urls import reverse

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _safe_hex(value, fallback):
    """Return a safe CSS hex color or a known-good fallback."""

    if isinstance(value, str) and _HEX_COLOR_RE.fullmatch(value.strip()):
        return value.strip()
    return fallback


def _object_launcher_items(user):
    """Return record objects the user can read for the app launcher."""

    if not user.is_authenticated:
        return []

    from .access import get_object_access
    from .models import Account, Opportunity

    object_configs = [
        {
            "label": "Accounts",
            "description": "View account records",
            "icon": "A",
            "url_name": "account_list",
            "keywords": "accounts customers people account",
            "model": Account,
        },
        {
            "label": "Opportunities",
            "description": "View opportunity records",
            "icon": "O",
            "url_name": "opportunity_list",
            "keywords": "opportunities deals pipeline opportunity",
            "model": Opportunity,
        },
    ]

    items = []
    for config in object_configs:
        if not get_object_access(user, config["model"]).can_read_records:
            continue
        items.append(
            {
                "label": config["label"],
                "description": config["description"],
                "icon": config["icon"],
                "url": reverse(config["url_name"]),
                "keywords": config["keywords"],
            }
        )
    return items


def site_branding(request):
    """Expose configured branding and global navigation metadata to templates."""

    branding = settings.SITE_BRANDING
    main_color = _safe_hex(branding.get("main_color"), "#0b5cab")
    secondary_color = _safe_hex(branding.get("secondary_color"), "#35a1ff")
    third_color = _safe_hex(branding.get("third_color"), "#20c997")

    return {
        "site_branding": {
            "name": branding.get("name") or "Force Sales",
            "main_color": main_color,
            "secondary_color": secondary_color,
            "third_color": third_color,
        },
        "object_launcher_items": _object_launcher_items(request.user),
    }
