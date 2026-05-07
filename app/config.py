import os


def clean_base_url(value: str | None) -> str:
    if not value:
        return ""

    value = value.strip()

    if value.endswith("/"):
        value = value[:-1]

    return value


ZERO2PRINT_BASE_URL = clean_base_url(
    os.getenv("ZERO2PRINT_BASE_URL", "")
)


def get_public_base_url(fallback_base_url: str | None = None) -> str:
    configured_url = clean_base_url(ZERO2PRINT_BASE_URL)

    if configured_url:
        return configured_url

    return clean_base_url(fallback_base_url)