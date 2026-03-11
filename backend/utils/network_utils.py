import socket

def get_actual_frontend_url(origin_header):
    """
    Detects the local IP address if the request is coming from localhost/127.0.0.1,
    allowing reset links to work across the local network.
    """
    base_url = origin_header or "http://localhost:5173"
    if "localhost" in base_url or "127.0.0.1" in base_url:
        try:
            # Create a dummy socket to find our LAN IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            base_url = base_url.replace("localhost", ip).replace("127.0.0.1", ip)
        except Exception:
            pass
    return base_url
