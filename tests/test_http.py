import gzip

import httpx
import pytest

from sc_jail.http import SourceError, SourceHTTP


def session(handler, budget=60):
    result = SourceHTTP("https://example.test", user_agent="Synthetic test", budget=budget)
    result.client.close()
    result.client = httpx.Client(base_url="https://example.test",
                                transport=httpx.MockTransport(handler))
    return result


def test_retryable_status_uses_bounded_retry_and_preserves_response(monkeypatch):
    calls, delays = [], []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, headers={"Retry-After": "1"}) if len(calls) < 3 else (
            httpx.Response(200, content=b"complete")
        )

    monkeypatch.setattr("sc_jail.http.time.sleep", delays.append)
    with session(handler) as client:
        assert client.request("GET", "/").content == b"complete"
    assert len(calls) == 3 and delays == [1, 1]


def test_decoded_stream_limit_and_headers():
    compressed = gzip.compress(b"x" * 2000)
    def handler(_):
        return httpx.Response(200, content=compressed, headers={"Content-Encoding": "gzip"})
    with session(handler) as client:
        with pytest.raises(SourceError, match="size limit"):
            client.request("GET", "/", max_bytes=100)
        response = client.request("GET", "/", max_bytes=3000)
        assert response.content == b"x" * 2000
        assert "content-encoding" not in response.headers


def test_retry_cannot_consume_remaining_budget(monkeypatch):
    sleeps = []
    monkeypatch.setattr("sc_jail.http.time.sleep", sleeps.append)
    with session(lambda _: httpx.Response(429, headers={"Retry-After": "15"}), budget=2) as client:
        with pytest.raises(SourceError, match="time budget"):
            client.request("GET", "/")
    assert not sleeps


def test_transport_failures_stop_after_three_attempts(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic", request=request)

    monkeypatch.setattr("sc_jail.http.time.sleep", lambda _: None)
    with session(handler) as client, pytest.raises(httpx.ReadTimeout):
        client.request("GET", "/")
    assert len(calls) == 3
