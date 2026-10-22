import importlib.util
import os
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import requests

os.environ["CLOUD_RUN_SERVICE_URL"] = "https://example.run.app"
os.environ["CLOUD_RUN_TEST_URL"] = "https://test.example.run.app"

module_path = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "dev_cloud_run_proxy.py"
)

spec = importlib.util.spec_from_file_location(
    "dev_cloud_run_proxy", module_path
)
proxy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(proxy)


@pytest.fixture
def local_proxy():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        proxy.ProxyHandler,
    )
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_unknown_endpoint_returns_404(local_proxy):
    response = requests.get(
        f"{local_proxy}/admin",
        timeout=5,
    )
    assert response.status_code == 404


def test_invalid_method_returns_405(local_proxy):
    response = requests.post(
        f"{local_proxy}/metrics",
        data=b"test",
        timeout=5,
    )
    assert response.status_code == 405


def test_invalid_download_path_returns_404(local_proxy):
    response = requests.get(
        f"{local_proxy}/predict/batch/invalid-id/download",
        timeout=5,
    )
    assert response.status_code == 404


def test_authentication_failure_returns_502(local_proxy, monkeypatch):
    def fail_authentication():
        raise OSError("Simulated authentication failure")

    monkeypatch.setattr(proxy, "get_identity_token", fail_authentication)

    response = requests.get(f"{local_proxy}/ready", timeout=5)
    assert response.status_code == 502


def test_invalid_content_length_returns_400(local_proxy):
    import socket

    port = int(local_proxy.rsplit(":", 1)[1])

    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall(
            b"POST /predict HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: abc\r\n"
            b"Connection: close\r\n\r\n"
        )
        result = sock.recv(4096)

    assert b"400" in result.split(b"\r\n", 1)[0]


def test_oversized_request_returns_413(local_proxy):
    import socket

    port = int(local_proxy.rsplit(":", 1)[1])

    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall(
            b"POST /predict HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: 20000001\r\n"
            b"Connection: close\r\n\r\n"
        )
        result = sock.recv(4096)

    assert b"413" in result.split(b"\r\n", 1)[0]


def test_post_without_content_length_returns_411(local_proxy):
    import socket

    port = int(local_proxy.rsplit(":", 1)[1])

    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall(
            b"POST /predict HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Connection: close\r\n\r\n"
        )
        result = sock.recv(4096)

    assert b"411" in result.split(b"\r\n", 1)[0]


def test_get_ready_forwards_request(local_proxy, monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setattr(
        proxy, "get_identity_token", lambda: "test-token"
    )

    upstream = Mock()
    upstream.status_code = 200
    upstream.content = b'{"status":"ready"}'
    upstream.headers = {"Content-Type": "application/json"}

    request_mock = Mock(return_value=upstream)
    monkeypatch.setattr(proxy.requests, "request", request_mock)

    response = requests.get(f"{local_proxy}/ready", timeout=5)

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

    kwargs = request_mock.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://test.example.run.app/ready"
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"


def test_csv_upload_preserves_body(local_proxy, monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setattr(
        proxy, "get_identity_token", lambda: "test-token"
    )

    upstream = Mock()
    upstream.status_code = 200
    upstream.content = b'{"rows_received":1}'
    upstream.headers = {"Content-Type": "application/json"}

    request_mock = Mock(return_value=upstream)
    monkeypatch.setattr(proxy.requests, "request", request_mock)

    response = requests.post(
        f"{local_proxy}/predict/batch",
        files={"file": ("sample.csv", b"Time,Amount\n0,10\n", "text/csv")},
        timeout=5,
    )

    assert response.status_code == 200
    assert response.json()["rows_received"] == 1

    kwargs = request_mock.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["url"].endswith("/predict/batch")
    assert b"sample.csv" in kwargs["data"]
    assert b"Time,Amount" in kwargs["data"]
    assert "multipart/form-data" in kwargs["headers"]["Content-Type"]
