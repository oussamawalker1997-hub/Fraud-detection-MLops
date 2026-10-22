import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

SERVICE_URL = os.environ.get("CLOUD_RUN_SERVICE_URL", "").rstrip("/")
TEST_URL = os.environ.get("CLOUD_RUN_TEST_URL", "").rstrip("/")

if not SERVICE_URL or not TEST_URL:
    raise SystemExit(
        "Set CLOUD_RUN_SERVICE_URL and CLOUD_RUN_TEST_URL before starting."
    )

HOST = "127.0.0.1"
PORT = 8081

def get_identity_token():
    return subprocess.check_output(
        [
            "gcloud",
            "auth",
            "print-identity-token",
            f"--audiences={SERVICE_URL}",
        ],
        text=True,
        stderr=subprocess.DEVNULL,
        timeout=20,
    ).strip()

class ProxyHandler(BaseHTTPRequestHandler):
    def handle_request(self):
        from urllib.parse import urlsplit

        parsed = urlsplit(self.path)
        path = parsed.path

        allowed = (
            path in ("/ready", "/health", "/metrics", "/predict", "/predict/batch")
            or (
                path.startswith("/predict/batch/")
                and path.endswith("/download")
                and len(path.split("/")) == 5
                and path.split("/")[3].isalnum()
            )
        )

        if not allowed or parsed.scheme or parsed.netloc:
            self.send_error(404, "Endpoint not allowed")
            return

        is_download = (
            path.startswith("/predict/batch/")
            and path.endswith("/download")
        )

        allowed_method = (
            self.command == "GET"
            and (path in ("/ready", "/health", "/metrics") or is_download)
        ) or (
            self.command == "POST"
            and path in ("/predict", "/predict/batch")
        )

        if not allowed_method:
            self.send_error(405, "Method not allowed")
            return

        raw_length = self.headers.get("Content-Length")

        try:
            length = int(raw_length) if raw_length is not None else 0
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if length < 0:
            self.send_error(400, "Invalid Content-Length")
            return

        if self.command == "POST" and raw_length is None:
            self.send_error(411, "Content-Length required")
            return

        if length > 20_000_000:
            self.send_error(413, "Request too large")
            return

        body = self.rfile.read(length) if length else None
        try:
            token = get_identity_token()
        except (subprocess.SubprocessError, OSError):
            self.send_error(502, "Cloud Run authentication failed")
            return

        headers = {"Authorization": f"Bearer {token}"}
        content_type = self.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type

        target = TEST_URL + self.path

        try:
            response = requests.request(
                method=self.command,
                url=target,
                headers=headers,
                data=body,
                timeout=120,
                allow_redirects=False,
            )
        except requests.RequestException:
            self.send_error(502, "Cloud Run request failed")
            return

        self.send_response(response.status_code)

        excluded = {
            "connection",
            "content-length",
            "content-encoding",
            "transfer-encoding",
            "set-cookie",
        }

        for key, value in response.headers.items():
            if key.lower() not in excluded:
                self.send_header(key, value)

        self.send_header("Content-Length", str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def log_message(self, format, *args):
        from urllib.parse import urlsplit
        print(
            f"{self.command} {urlsplit(self.path).path}",
            flush=True,
        )


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ProxyHandler)
    print(f"DEV_PROXY_READY http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
