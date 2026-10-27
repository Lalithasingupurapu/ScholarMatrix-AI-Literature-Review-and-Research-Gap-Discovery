import os
import ssl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# Create an SSL context that ignores local verification issues common in Windows dev environments
def get_ssl_context():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return ssl._create_unverified_context()

DEFAULT_USER_AGENT = "ScholarMatrixAI/1.0 (academic-research-assistant; mailto:researcher@project.edu)"
