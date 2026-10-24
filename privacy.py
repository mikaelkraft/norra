"""
Norra AI - Privacy Policy Page (Python Entrypoint)
"""
import sys
import os

# Ensure local imports work regardless of current working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import static_pages

def get_html() -> str:
    return static_pages.get_privacy_html()

def application(environ, start_response):
    """WSGI callable interface."""
    body = get_html().encode("utf-8")
    status = "200 OK"
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body)))
    ]
    start_response(status, headers)
    return [body]

if __name__ == "__main__":
    if "GATEWAY_INTERFACE" in os.environ:
        # CGI mode
        print("Content-Type: text/html; charset=utf-8\n")
        print(get_html())
    else:
        # CLI print mode
        print(get_html())
