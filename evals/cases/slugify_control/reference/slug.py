import re


def slugify(title):
    """Lowercase, words joined by single hyphens, no leading or trailing hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
