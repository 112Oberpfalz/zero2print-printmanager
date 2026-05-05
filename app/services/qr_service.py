from pathlib import Path

import qrcode


QR_DIR = Path("data/qr")


def create_qr_code(content: str, filename: str) -> Path:
    QR_DIR.mkdir(parents=True, exist_ok=True)

    qr_path = QR_DIR / filename

    img = qrcode.make(content)
    img.save(qr_path)

    return qr_path