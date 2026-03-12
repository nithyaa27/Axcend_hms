import os

def get_actual_frontend_url(origin_header):
    """
    Returns the frontend URL. Prioritizes the FRONTEND_URL environment variable,
    then the Origin header, and finally defaults to http://localhost:5173.
    """
    env_url = os.getenv("FRONTEND_URL")
    if env_url:
        return env_url.rstrip("/")
        
    base = origin_header or "http://localhost:5173"
    return base.rstrip("/")
