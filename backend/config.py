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


def get_serper_api_key() -> str:
    """Return the Serper API key from environment or local .env file."""
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if key:
        return key
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if key:
        return key
    env_file = BASE_DIR / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k_clean = k.strip()
                if k_clean in ("SERPER_API_KEY", "SERPAPI_API_KEY"):
                    val = v.strip().strip("'\"")
                    if val:
                        return val
        except Exception:
            pass
    return ""


def get_serpapi_api_key() -> str:
    """Return API key (Serper or legacy SerpApi) for backwards compatibility."""
    return get_serper_api_key()
