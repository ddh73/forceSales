import re

from django.conf import settings

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _safe_hex(value, fallback):
    """Return a safe CSS hex color or a known-good fallback."""

    if isinstance(value, str) and _HEX_COLOR_RE.fullmatch(value.strip()):
        return value.strip()
    return fallback


def site_branding(request):
    """Expose the configured site name and theme colors to templates."""

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
        }
    }
