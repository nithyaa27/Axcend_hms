import os

# ==========================================================
# Network Utilities
# ==========================================================
# Provides helper functions for network and URL resolution,
# specifically for dynamic frontend address detection.

def get_actual_frontend_url(origin_header):
    """
    Returns the frontend URL. Prioritizes the FRONTEND_URL environment variable,
    then the Origin header.
    """
    env_url = os.getenv("FRONTEND_URL")
    if env_url:
        return env_url.rstrip("/")
        
    base = origin_header or ""
    return base.rstrip("/")
