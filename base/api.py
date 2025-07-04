import asyncio
import concurrent.futures
import json
import logging
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict

LOGGER = logging.getLogger(__name__)
HANDLER = logging.StreamHandler()
FORMATTER = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - [%(processName)s:%(module)s:%(lineno)d] - %(funcName)s - %(message)s"
)
HANDLER.setFormatter(fmt=FORMATTER)
LOGGER.addHandler(hdlr=HANDLER)
LOGGER.setLevel(level=logging.DEBUG)


# noinspection PyPep8Naming
class SimpleAPIHandler(SimpleHTTPRequestHandler):
    """A simple HTTP request handler that serves a basic API endpoint.

    This handler demonstrates how to handle GET requests, set response headers and cookies,
    and return JSON responses without using any external frameworks.
    """

    # noinspection PyShadowingBuiltins
    def log_message(self, format, *args):
        """Log an arbitrary message using the configured LOGGER instead of printing to stderr.

        Args:
            format (str): A printf-style format string for the log message.
            *args: Variable length argument list to be formatted into the message.
        """
        LOGGER.info("%s - %s\n" % (self.client_address[0], format % args))

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set multiple HTTP headers in the response.

        Args:
            headers: A dictionary of HTTP header key-value pairs to set.
        """
        for key, value in headers.items():
            self.send_header(key, value)

    def set_cookies(
        self,
        cookies: Dict[str, str],
        path: str = "/",
        domain: str = None,
        http_only: bool = False,
        secure: bool = False,
        max_age: int = 3_600,
        expires: str | datetime = None,
    ) -> None:
        """Set multiple cookies in the HTTP response.

        Args:
            cookies: A dictionary of cookie name-value pairs to set.
            path: The URL path for which the cookie is valid. Default is "/".
            domain: The domain that can access the cookie.
            http_only: If True, marks the cookie as HttpOnly. Default is False.
            secure: If True, the cookie is sent only over HTTPS. Default is False.
            max_age: Lifetime of the cookie in seconds. Default is 3600 (1 hour).
            expires: A specific expiration date/time for the cookie as a proper string or datetime object.

        Note:
            This function only queues `Set-Cookie` headers. You must call `end_headers()`
            afterward in your main handler method.
        """
        for key, value in cookies.items():
            cookie = f"{key}={value}"

            if path:
                cookie += f"; Path={path}"
            if domain:
                cookie += f"; Domain={domain}"
            if http_only:
                cookie += "; HttpOnly"
            if secure:
                cookie += "; Secure"
            if max_age:
                cookie += f"; Max-Age={max_age}"
            if expires:
                if isinstance(expires, datetime):
                    expires = expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
                cookie += f"; Expires={expires}"
            self.send_header("Set-Cookie", cookie)

    def set_defaults(self) -> None:
        """Logs the headers and cookies."""
        if cookie_header := self.headers.get("Cookie"):
            cookies = {}
            for pair in cookie_header.split(";"):
                if "=" in pair:
                    key, value = pair.strip().split("=", 1)
                    cookies[key] = value
            LOGGER.debug(cookies)
        LOGGER.debug(dict(self.headers))

        self.send_response(200)
        self.set_headers(
            {"Content-type": "application/json", "X-Server": "NoFrameworkServer"}
        )
        self.set_cookies({"visited": "true"})
        self.end_headers()

    def do_DELETE(self) -> None:
        """Handle DELETE requests to the server."""
        self.set_defaults()
        self.wfile.write(json.dumps({"message": "🔴 DELETE received"}).encode())

    def do_HEAD(self) -> None:
        """Handle HEAD requests to the server."""
        self.set_defaults()
        self.wfile.write(json.dumps({"message": "🟣 HEAD received"}).encode())

    def do_OPTIONS(self) -> None:
        """Handle OPTIONS requests to the server."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "⚪ OPTIONS received"}).encode())

    def do_POST(self) -> None:
        """Handle POST requests to the server."""
        self.set_defaults()
        self.wfile.write(json.dumps({"message": "🟡 POST received"}).encode())

    def do_PUT(self) -> None:
        """Handle PUT requests to the server."""
        self.set_defaults()
        self.wfile.write(json.dumps({"message": "🔵 PUT received"}).encode())

    def do_PATCH(self) -> None:
        """Handle PATCH requests to the server."""
        self.set_defaults()
        self.wfile.write(json.dumps({"message": "🟠 PATCH received"}).encode())

    def do_GET(self) -> None:
        """Handle GET requests to the server."""
        if self.path == "/":
            self.set_defaults()
            self.wfile.write(json.dumps({"message": "🟢 GET received"}).encode())
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')


# noinspection PyTypeChecker,HttpUrlsUsage
def run(
    server_class=HTTPServer,
    handler_class=SimpleAPIHandler,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Start the HTTP server and listen for incoming requests in synchronous mode.

    Args:
        server_class: The server class to use.
        handler_class: The request handler class to use.
        host: The host address to bind to. Default is '0.0.0.0'.
        port: The port number to listen on. Default is 8080.
    """
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on http://{host}:{port}")
    httpd.serve_forever(0.5)


# noinspection PyTypeChecker,HttpUrlsUsage
async def run_async(
    server_class=HTTPServer,
    handler_class=SimpleAPIHandler,
    host: str = "0.0.0.0",
    port: str = 8080,
) -> None:
    """Start the HTTP server and listen for incoming requests in asynchronous mode.

    Args:
        server_class: The server class to use.
        handler_class: The request handler class to use.
        host: The host address to bind to. Default is '0.0.0.0'.
        port: The port number to listen on. Default is 8080.
    """
    loop = asyncio.get_running_loop()
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on http://{host}:{port}/")
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, httpd.serve_forever, 0.5)


if __name__ == "__main__":
    asyncio.run(run_async())
