"""Interface the HTTP server of a Solis Logger device (e.g. WiFi stick) for local (non-cloud) status access."""

from http import HTTPStatus
import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class AuthorizationFailed(Exception):
    """HTTP authorization towards Solis Logger failed."""


class ConnectionFailed(Exception):
    """HTTP connection to Solis Logger failed."""


def parse_status_html(status_html: str) -> dict:
    """Scrape relevant information from the status.html output of a Solis logger. Return a dict."""
    result = {}
    for line in [
        line.split(" ", 1)[1].split(";", 1)[0]
        for line in status_html.splitlines()
        if line.startswith("var")
    ]:
        [variable, value] = [a.strip() for a in line.split("=", 2)]
        if [x for x in ("webdata", "cover", "status") if variable.startswith(x)]:
            result[variable] = value.strip('"')
    return result


def solis_logger_url(host: str) -> str:
    """Compute URL for local Solis logger based on host."""
    clean_host = host.strip(" /:")
    for prefix in ("http://", "https://", "http:", "https:"):
        if clean_host.startswith(prefix):
            clean_host = clean_host[len(prefix) :]
    clean_host = clean_host.strip("/:")
    return "http://" + clean_host + "/status.html"


class SolisLocalHttpAPI:
    """Access Solis logger via local HTTP, i.e. built-in server on the logger device."""

    def __init__(self, data) -> None:
        """Initialize."""
        self.host = data["host"]
        self.url = solis_logger_url(self.host)
        self.username = data["username"]
        self.password = data["password"]

    async def load_status(self) -> dict:
        """Test if we can authenticate with the host."""
        async with aiohttp.request(
            "GET",
            self.url,
            auth=aiohttp.BasicAuth(self.username, self.password),
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == HTTPStatus.OK:
                return parse_status_html(await response.text())
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise AuthorizationFailed
            raise ConnectionFailed
