#!/usr/bin/env python3
"""
Odd requests to a running stack. Plain Python 3, no packages to install.

    cd infrastructure
    python tests/odd_requests.py

A client mistake must get the RIGHT 4xx status and the shared error JSON (timestamp, status, code, message, path,
refreshable, details), never a 500. 500 means "the server is broken": it starts alarms and hides real problems.
For each of the five services it sends: an unknown address (logged in and not), a wrong HTTP method, a body that is
not JSON and a wrong content type, and checks the status and the shape of the answer.

Settings (all optional): SMOKE_BASE_URL (default http://localhost), and SMOKE_<NAME>_URL for one service somewhere
else, with NAME = USER, PRODUCT, ORDER, NOTIFICATION or PAYMENT. The first admin of
environments/local/env/user-service.env is used. Exit code 0 = everything passed.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "..", "environments", "local", "env", "user-service.env")
BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").rstrip("/")
SHAPE = {"timestamp", "status", "code", "message", "path", "refreshable", "details"}

# name -> (address of a JSON POST, address that has no PUT)
SERVICES = {
    "user": ("/auth/login", "/auth/login"),
    "product": ("/admin/categories", "/admin/categories"),
    "order": ("/orders", "/admin/orders"),
    "notification": ("/push-devices", "/push-devices"),
    "payment": ("/admin/courier-receipts", "/admin/payments"),
}


def read_env(path):
    values = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line.strip())
            if m:
                values[m.group(1)] = m.group(2)
    return values


def call(method, url, cookie=None, data=None, content_type=None):
    headers = {"Content-Type": content_type} if content_type else {}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), e.headers


def main():
    env = read_env(ENV_FILE)
    user_url = os.environ.get("SMOKE_USER_URL", BASE).rstrip("/")
    body = json.dumps({"email": env["ADMIN_BOOTSTRAP_EMAIL"], "password": env["ADMIN_BOOTSTRAP_PASSWORD"]}).encode()
    status, _, headers = call("POST", user_url + "/api/v1/user/auth/login", data=body, content_type="application/json")
    admin = next((v.split(";")[0] for v in headers.get_all("Set-Cookie") or [] if v.startswith("access_token=")), None)
    if status != 200 or admin is None:
        print("Cannot log in as the first admin. Is the stack up?")
        return 1

    checks, bad = 0, []

    def check(service, label, status, headers, raw, expected_status, expected_code, need_allow=False):
        nonlocal checks
        checks += 1
        try:
            answer = json.loads(raw) if raw else None
        except ValueError:
            answer = None
        ok = (status == expected_status and isinstance(answer, dict) and SHAPE <= set(answer)
              and answer.get("status") == status and answer.get("code") == expected_code
              and (not need_allow or bool(headers.get("Allow"))))
        print(("PASS  " if ok else "FAIL  ") + f"{service}: {label} -> {status}")
        if not ok:
            bad.append((service, label, status, raw[:150]))

    for name, (json_post, no_put) in SERVICES.items():
        url = os.environ.get(f"SMOKE_{name.upper()}_URL", BASE).rstrip("/") + f"/api/v1/{name}"
        s, raw, h = call("GET", url + "/does-not-exist", admin)
        check(name, "an address that does not exist (logged in)", s, h, raw, 404, "NOT_FOUND")
        s, raw, h = call("GET", url + "/does-not-exist")
        check(name, "an address that does not exist (not logged in)", s, h, raw, 401, "ACCESS_TOKEN_MISSING")
        s, raw, h = call("PUT", url + no_put, admin)
        check(name, "a method the address does not know", s, h, raw, 405, "METHOD_NOT_ALLOWED", need_allow=True)
        s, raw, h = call("POST", url + json_post, admin, b"hello", "text/plain")
        check(name, "a wrong content type", s, h, raw, 415, "UNSUPPORTED_MEDIA_TYPE")
        if name != "payment":  # its only POST reads a multipart form, not JSON
            s, raw, h = call("POST", url + json_post, admin, b"{not json", "application/json")
            check(name, "a body that is not JSON", s, h, raw, 400, "INVALID_REQUEST")

    print(f"\n{checks - len(bad)}/{checks} answers are right")
    for b in bad:
        print("  WRONG:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
