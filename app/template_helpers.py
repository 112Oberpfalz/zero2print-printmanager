from pathlib import Path


def status_class(status: str) -> str:
    if not status:
        return "status-default"

    normalized = status.strip().lower()

    mapping = {
        "anfrage": "status-request",
        "datei prüfen": "status-check",
        "bereit zum druck": "status-ready",
        "druck läuft": "status-running",
        "druck fertig": "status-done",
        "nacharbeit": "status-post",
        "fertig": "status-finished",
        "erledigt": "status-finished",
        "archiviert": "status-archived",
        "fehler": "status-error",
    }

    return mapping.get(normalized, "status-default")


def format_file_size(file_path: str) -> str:
    if not file_path:
        return "-"

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        return "-"

    size_bytes = path.stat().st_size

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kb = size_bytes / 1024

    if size_kb < 1024:
        return f"{size_kb:.1f} KB"

    size_mb = size_kb / 1024

    if size_mb < 1024:
        return f"{size_mb:.2f} MB"

    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"