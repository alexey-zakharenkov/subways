import http.client
import urllib.error
import urllib.request
from typing import Any


def urlopen_or_raise(
    url: str | urllib.request.Request,
    *,
    error_prefix: str = "HTTP request failed",
    **kwargs: Any,
) -> http.client.HTTPResponse:
    try:
        return urllib.request.urlopen(url, **kwargs)
    except urllib.error.HTTPError as e:
        raise Exception(f"{error_prefix}: HTTP {e.code}") from e
