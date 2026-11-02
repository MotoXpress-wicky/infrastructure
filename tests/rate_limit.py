#!/usr/bin/env python3
"""
Rate limit check for a running stack. Plain Python 3, no packages to install.

    cd infrastructure
    python tests/rate_limit.py

It tries to break the limits of user-service the way an attacker would:
  * 5 wrong passwords for one email in 15 minutes, then 429 (the RIGHT password is blocked too)
  * other emails are not affected
  * 3 password reset requests per email per hour
  * the 429 answer has the shared error JSON and a Retry-After header

Two more checks need a DIFFERENT client address for every request. Nginx always writes the real address of the caller
into X-Forwarded-For, so they only work when you talk to user-service directly (for example a copy running in IntelliJ):

    SMOKE_DIRECT=1 SMOKE_USER_URL=http://localhost:8080 python tests/rate_limit.py

  * 30 logins per address per 15 minutes
  * 5 registrations per address per hour

Every run uses new email addresses. The limits stay in Redis for 15 minutes to 1 hour, so a second run within the hour
can fail on the reset or register check. That is the limit working, not a bug: wait, or empty Redis (FLUSHALL).
The first admin from environments/local/env/user-service.env is used for the "others are not affected" check.
The captcha must be off or use Cloudflare's test keys (the local default).
Exit code 0 = everything passed.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "..", "environments", "local", "env", "user-service.env")
USER = os.environ.get("SMOKE_USER_URL", os.environ.get("SMOKE_BASE_URL", "http://localhost")).rstrip("/")
DIRECT = os.environ.get("SMOKE_DIRECT") == "1"

SUFFIX = uuid.uuid4().hex[:6]
SUFFIX_NUM = int(SUFFIX[:2], 16)
checks, failures = 0, []
_next_ip = [0]


def read_env(path):
    values = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line.strip())
            if m:
                values[m.group(1)] = m.group(2)
    return values


def new_ip():
    """A fresh client address (only used when DIRECT, see above)."""
    _next_ip[0] += 1
    return f"10.77.{SUFFIX_NUM}.{_next_ip[0]}"


def post(path, body, ip=None):
    headers = {"Content-Type": "application/json"}
    if DIRECT and ip:
        headers["X-Forwarded-For"] = ip
    req = urllib.request.Request(USER + path, data=json.dumps(body).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), e.headers


def login(email, password, ip=None):
    return post("/api/v1/user/auth/login", {"email": email, "password": password}, ip)


def register(email, ip=None):
    return post("/api/v1/user/auth/register",
                {"name": "Rate Test", "email": email, "password": "some-password-1", "captchaToken": "XXXX.DUMMY.TOKEN.XXXX"}, ip)


def check(name, ok, detail=""):
    global checks
    checks += 1
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "\n        -> " + str(detail)[:400]))
    if not ok:
        failures.append(name)


def main():
    env = read_env(ENV_FILE)
    print(f"rate limit check, run {SUFFIX} ({'direct, one address per request' if DIRECT else 'through the front door, one address'})\n")

    # 1. per email: 5 tries in 15 minutes, whoever calls
    victim = f"victim.{SUFFIX}@example.com"
    status, raw, _ = register(victim, new_ip())
    check("1. a test account is created", status in (200, 201), (status, raw[:200]))
    codes = [login(victim, "wrong-password-1", new_ip())[0] for _ in range(5)]
    check("1. 5 wrong passwords for one email: each answered 401", codes == [401] * 5, codes)
    status, raw, headers = login(victim, "wrong-password-1", new_ip())
    body = json.loads(raw) if raw.startswith("{") else {}
    shape = {"timestamp", "status", "code", "message", "path", "refreshable", "details"}
    check("1. the 6th try: 429 with the shared error JSON", status == 429 and body.get("code") == "RATE_LIMITED" and set(body) >= shape, (status, raw[:200]))
    check("1. ... and a Retry-After header with a number of seconds", headers.get("Retry-After", "").isdigit() and int(headers["Retry-After"]) > 0, headers.get("Retry-After"))
    status, raw, _ = login(victim, "some-password-1", new_ip())
    check("1. even the RIGHT password is blocked for that email (guessing cannot be finished by luck)", status == 429, (status, raw[:150]))

    # 2. other people are not affected
    status, raw, headers = login(env["ADMIN_BOOTSTRAP_EMAIL"], env["ADMIN_BOOTSTRAP_PASSWORD"], new_ip())
    check("2. another email logs in normally while the victim is blocked", status == 200 and "access_token" in "".join(headers.get_all("Set-Cookie") or []), (status, raw[:150]))

    # 3. password reset: 3 per hour per email
    codes = [post("/api/v1/user/auth/forgot-password", {"email": victim, "captchaToken": "XXXX.DUMMY.TOKEN.XXXX"}, new_ip())[0] for _ in range(3)]
    check("3. 3 reset requests for one email: accepted", codes == [200] * 3, codes)
    status, raw, _ = post("/api/v1/user/auth/forgot-password", {"email": victim, "captchaToken": "XXXX.DUMMY.TOKEN.XXXX"}, new_ip())
    check("3. the 4th: 429", status == 429, (status, raw[:150]))

    if DIRECT:
        # 4. per address: 30 logins in 15 minutes
        ip = new_ip()
        codes = [login(f"nobody{i}.{SUFFIX}@example.com", "wrong-password-1", ip)[0] for i in range(30)]
        check("4. 30 logins from one address (30 different emails): each answered 401", codes == [401] * 30, sorted(set(codes)))
        check("4. the 31st from that address: 429", login(f"nobody31.{SUFFIX}@example.com", "wrong-password-1", ip)[0] == 429)
        check("4. a different address is not affected", login(f"nobody32.{SUFFIX}@example.com", "wrong-password-1", new_ip())[0] == 401)

        # 5. per address: 5 registrations per hour
        ip = new_ip()
        codes = [register(f"reg{i}.{SUFFIX}@example.com", ip)[0] for i in range(5)]
        check("5. 5 registrations from one address: accepted", all(c in (200, 201) for c in codes), codes)
        check("5. the 6th registration from that address: 429", register(f"reg6.{SUFFIX}@example.com", ip)[0] == 429)
    else:
        print("\n(4 and 5, the limits per address, were skipped: set SMOKE_DIRECT=1 and talk to user-service directly)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nThe check stopped: {exc!r}")
        failures.append("crash")
    print(f"\n{checks - len([f for f in failures if f != 'crash'])}/{checks} checks passed")
    sys.exit(1 if failures else 0)
