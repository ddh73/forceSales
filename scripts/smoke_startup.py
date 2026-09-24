"""Exercise real Linux startup, login, static serving, and restart persistence."""
import http.cookiejar
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent.parent


def main():
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "persistent" / "db.sqlite3"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ)
        env.pop("DATABASE_URL", None)
        env.update(
            PORT=str(port), DJANGO_SQLITE_PATH=str(database),
            DJANGO_DEBUG="False", DJANGO_SECRET_KEY="ci-only-secret-key",
            DJANGO_SUPERUSER_USERNAME="smoke-admin",
            DJANGO_SUPERUSER_PASSWORD="ci-only-password!",
        )
        base = f"http://127.0.0.1:{port}"
        for attempt in range(2):
            if attempt:
                env["DJANGO_SUPERUSER_PASSWORD"] = "must-not-reset-the-password"
            process = subprocess.Popen(["bash", str(ROOT / "startup.sh")], cwd=directory, env=env)
            try:
                opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
                deadline = time.monotonic() + 60
                while True:
                    try:
                        with opener.open(base + "/accounts/login/", timeout=2) as response:
                            page = response.read().decode()
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if process.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError("Startup failed before login became available")
                        time.sleep(0.5)
                token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
                body = urllib.parse.urlencode({
                    "csrfmiddlewaretoken": token, "username": "smoke-admin", "password": "ci-only-password!",
                }).encode()
                with opener.open(base + "/accounts/login/", data=body, timeout=10) as response:
                    assert response.status == 200 and response.url.endswith("/dashboard/"), response.url
                stylesheet = re.search(r'href="([^"]+\.css)"', page).group(1)
                with opener.open(base + stylesheet, timeout=10) as response:
                    assert response.status == 200 and "text/css" in response.headers["Content-Type"]
                with sqlite3.connect(database) as connection:
                    assert connection.execute("SELECT COUNT(*) FROM auth_user").fetchone()[0] == 1
                    assert connection.execute("SELECT COUNT(*) FROM django_migrations WHERE app='crm'").fetchone()[0] >= 9
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        print("Startup, migrations, login, CSS, and restart persistence passed.")


if __name__ == "__main__":
    main()
