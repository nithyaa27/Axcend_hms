import os


def get_actual_frontend_url(origin_header):
    configured_url = os.getenv("FRONTEND_PUBLIC_URL", "").strip()
    base_url = configured_url or (origin_header or "http://localhost:5173")
    return base_url.rstrip("/")
