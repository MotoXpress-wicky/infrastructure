#!/usr/bin/env python3
"""
Smoke test for a running motoXpress stack. Plain Python 3, no packages to install.

    cd infrastructure
    docker compose -f environments/local/docker-compose.yml up -d     (wait until the services are healthy)
    python tests/smoke.py

It uses the real HTTP API, like the two web sites do, and walks through a whole shop day:

  1. the first admin logs in (made by user-service at start-up)
  2. a customer registers  -> welcome email          (user-service -> RabbitMQ -> notification-service)
  3. forgot password       -> reset email, reset link works, "password changed" email
  4. the admin adds a part with a photo (object storage) and the photo is public through Nginx
  5. the customer orders   -> payment PENDING, confirmation email          (order-service -> payment-service)
  6. the admin ships       -> payment knows courier + tracking number, shipped email
  7. the admin marks it delivered -> payment COLLECTED -> order shows COLLECTED
  8. the admin enters the courier receipt (with a PDF) -> payment PAID -> order shows PAID
  9. a cancelled order and a returned parcel -> payments CANCELLED, stock comes back
 10. who may call what: 401 without login, 403 for a customer on admin URLs

Every run uses new names (a random suffix), so you can run it again and again.
Exit code 0 = everything passed.

Settings (all optional):
  SMOKE_BASE_URL       the customer site, default http://localhost (the API of every service is reachable there)
  SMOKE_<NAME>_URL     override one service: USER, PRODUCT, ORDER, PAYMENT  (for services running outside Docker)
  SMOKE_MAIL_URL       Mailpit, default: the same Nginx with the Host header mail.localhost
  SMOKE_MAIL_FILE      a .jsonl file with {"to": [...], "subject": ..., "body": ...} per line, instead of Mailpit
  SMOKE_SKIP_MEDIA=1   do not fetch the photo through /media (when Nginx is not in front)
  SMOKE_WAIT_SECONDS   how long to wait for an event to arrive, default 40
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "..", "environments", "local", "env", "user-service.env")

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").rstrip("/")
USER = os.environ.get("SMOKE_USER_URL", BASE).rstrip("/")
PRODUCT = os.environ.get("SMOKE_PRODUCT_URL", BASE).rstrip("/")
ORDER = os.environ.get("SMOKE_ORDER_URL", BASE).rstrip("/")
PAYMENT = os.environ.get("SMOKE_PAYMENT_URL", BASE).rstrip("/")
MAIL_URL = os.environ.get("SMOKE_MAIL_URL", "").rstrip("/")
MAIL_FILE = os.environ.get("SMOKE_MAIL_FILE", "")
WAIT = int(os.environ.get("SMOKE_WAIT_SECONDS", "40"))
SKIP_MEDIA = os.environ.get("SMOKE_SKIP_MEDIA") == "1"

SUFFIX = uuid.uuid4().hex[:6]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.4\n% receipt\n" + b"0" * 64

failures, checks = [], 0


# ---------------------------------------------------------------- small helpers

def read_env(path):
    values = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line.strip())
            if m:
                values[m.group(1)] = m.group(2)
    return values


def call(method, url, cookie=None, body=None, fields=None, files=None, headers=None, raw=False):
    """One HTTP call. JSON in, JSON out. fields/files = multipart form. Returns (status, body, response headers)."""
    data, hdrs = None, dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    if fields is not None or files is not None:
        boundary = "----smoke" + uuid.uuid4().hex
        out = b""
        for k, v in (fields or {}).items():
            for item in (v if isinstance(v, list) else [v]):
                out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{item}\r\n'.encode()
        for k, (fname, content, ctype) in (files or {}).items():
            out += (f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'
                    f"Content-Type: {ctype}\r\n\r\n").encode() + content + b"\r\n"
        data = out + f"--{boundary}--\r\n".encode()
        hdrs["Content-Type"] = "multipart/form-data; boundary=" + boundary
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content, status, rh = resp.read(), resp.status, resp.headers
    except urllib.error.HTTPError as e:
        content, status, rh = e.read(), e.code, e.headers
    if raw:
        return status, content, rh
    text = content.decode(errors="replace")
    try:
        return status, (json.loads(text) if text else None), rh
    except ValueError:
        return status, text, rh


def check(name, ok, detail=""):
    global checks
    checks += 1
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "\n        -> " + str(detail)[:500]))
    if not ok:
        failures.append(name)


def wait_for(fn, seconds=None):
    """Events are asynchronous: poll until fn() returns something truthy."""
    end = time.time() + (seconds or WAIT)
    while time.time() < end:
        try:
            value = fn()
        except Exception:  # the service may not answer for a moment
            value = None
        if value:
            return value
        time.sleep(1)
    return None


def login(email, password):
    status, body, headers = call("POST", USER + "/api/v1/user/auth/login", body={"email": email, "password": password})
    for value in headers.get_all("Set-Cookie") or []:
        if value.startswith("access_token="):
            return value.split(";")[0]
    return None


# ---------------------------------------------------------------- emails (Mailpit, or a file)

def all_mails():
    """[{to: [...], subject, body}] from the file, or from Mailpit's REST API."""
    if MAIL_FILE:
        if not os.path.exists(MAIL_FILE):
            return []
        with open(MAIL_FILE, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    base = MAIL_URL or BASE
    headers = {} if MAIL_URL else {"Host": "mail.localhost"}
    status, listing, _ = call("GET", base + "/api/v1/messages?limit=200", headers=headers)
    if status != 200 or not isinstance(listing, dict):
        raise RuntimeError(f"Mailpit did not answer as expected: {status}")
    out = []
    for item in listing.get("messages") or listing.get("Messages") or []:
        mail_id = item.get("ID") or item.get("Id")
        to = [(t.get("Address") or "") for t in (item.get("To") or [])]
        status, detail, _ = call("GET", f"{base}/api/v1/message/{mail_id}", headers=headers)
        body = (detail.get("HTML") or detail.get("Text") or "") if isinstance(detail, dict) else ""
        out.append({"to": to, "subject": item.get("Subject") or "", "body": body})
    return out


def mail_to(address, *needles):
    for m in all_mails():
        text = (m["subject"] + " " + m["body"]).lower()
        if address in m["to"] and all(n.lower() in text for n in needles):
            return m
    return None


# ---------------------------------------------------------------- the day

def main():
    env = read_env(ENV_FILE)
    admin_email, admin_password = env["ADMIN_BOOTSTRAP_EMAIL"], env["ADMIN_BOOTSTRAP_PASSWORD"]

    print(f"motoXpress smoke test, run {SUFFIX}\n")

    # 1. the first admin
    admin = wait_for(lambda: login(admin_email, admin_password), 60)
    check("1. the first admin logs in (created by user-service at start-up)", admin is not None)
    if admin is None:
        print("\nCannot go on without an admin. Is the stack up, and is ADMIN_BOOTSTRAP_EMAIL set?")
        return

    # 2 + 3. the customer: register, welcome email, password reset
    email = f"smoke.{SUFFIX}@example.com"
    status, body, _ = call("POST", USER + "/api/v1/user/auth/register",
                           body={"name": "Amara Silva", "email": email, "password": "customer-pass-2", "captchaToken": "XXXX.DUMMY.TOKEN.XXXX"})
    check("2. a customer registers", status in (200, 201), (status, body))
    check("2. user.registered -> a welcome email arrives", wait_for(lambda: mail_to(email, "welcome")) is not None)

    call("POST", USER + "/api/v1/user/auth/forgot-password", body={"email": email, "captchaToken": "XXXX.DUMMY.TOKEN.XXXX"})
    reset = wait_for(lambda: mail_to(email, "reset your password"))
    check("3. user.password.reset -> the reset email arrives", reset is not None)
    token = None
    if reset:
        found = re.search(r"reset-password\?token=([A-Za-z0-9_-]+)", reset["body"])
        token = found.group(1) if found else None
    check("3. the email holds a reset link with a token", token is not None)
    if token:
        status, body, _ = call("POST", USER + "/api/v1/user/auth/reset-password", body={"token": token, "newPassword": "brand-new-pass-3"})
        check("3. the reset link works", status == 200, (status, body))
        check("3. user.password.changed -> the confirmation email arrives", wait_for(lambda: mail_to(email, "password was changed")) is not None)
    customer = login(email, "brand-new-pass-3") or login(email, "customer-pass-2")
    check("3. the customer logs in", customer is not None)

    # 4. catalog with a photo
    status, cat, _ = call("POST", PRODUCT + "/api/v1/product/admin/categories", admin, {"name": f"Brakes {SUFFIX}"})
    check("4. the admin adds a category", status == 201, (status, cat))
    status, prod, _ = call("POST", PRODUCT + "/api/v1/product/admin/products", admin, {
        "partNumber": f"BP-{SUFFIX}", "name": "Front brake pad set", "categoryId": cat["id"], "price": 3500.00,
        "initialStock": 5, "universalFit": True, "condition": "NEW"})
    check("4. the admin adds a part with 5 in stock", status == 201 and prod.get("stockQty") == 5, (status, prod))
    pid = prod["id"]
    status, photo, _ = call("POST", PRODUCT + f"/api/v1/product/admin/products/{pid}/photos", admin, files={"file": ("pad.png", PNG, "image/png")})
    check("4. the admin uploads a photo (object storage)", status == 201 and photo.get("url"), (status, photo))
    if status == 201 and not SKIP_MEDIA:
        url = photo["url"] if photo["url"].startswith("http") else BASE + photo["url"]
        status, content, headers = call("GET", url, raw=True)
        check("4. the photo is public through Nginx (/media/products/...), byte for byte", status == 200 and content == PNG, (status, url))
    status, body, _ = call("GET", PRODUCT + f"/api/v1/product/products/{pid}")
    check("4. a visitor sees the part and its photo without login", status == 200 and len(body["photos"]) == 1, (status, body))

    # 5-8. one order, from the cart to the money
    address = {"phone": "0771234567", "addressLine": "12 Galle Road", "city": "Colombo", "district": "Colombo"}

    def place(qty):
        st, order, _ = call("POST", ORDER + "/api/v1/order/orders", customer, {"lines": [{"productId": pid, "quantity": qty}], "address": address})
        if st != 201:
            raise RuntimeError(f"checkout failed: {st} {order}")
        return order

    def payment_of(reference):
        st, page, _ = call("GET", PAYMENT + f"/api/v1/payment/admin/payments?reference={reference}", admin)
        return page["content"][0] if st == 200 and page["content"] else None

    def order_of(order_no):
        return call("GET", ORDER + f"/api/v1/order/admin/orders/{order_no}", admin)[1]

    def payment_with(reference, **expected):
        def probe():
            p = payment_of(reference)
            return p if p and all(p.get(k) == v for k, v in expected.items()) else None
        return probe

    def order_with(order_no, **expected):
        def probe():
            o = order_of(order_no)
            return o if isinstance(o, dict) and all(o.get(k) == v for k, v in expected.items()) else None
        return probe

    o1 = place(1)
    no1 = o1["orderNo"]
    pay = wait_for(payment_with(no1, status="PENDING"))
    check("5. order.placed -> payment-service makes a PENDING payment with the right amount", pay is not None and pay["amount"] == o1["total"], pay)
    check("5. order.placed -> the confirmation email arrives", wait_for(lambda: mail_to(email, no1, "received")) is not None)
    status, body, _ = call("GET", PRODUCT + f"/api/v1/product/admin/products/{pid}", admin)
    check("5. stock went down to 4", body.get("stockQty") == 4, body)

    status, body, _ = call("POST", ORDER + "/api/v1/order/admin/shipments", admin,
                           fields={"orderNo": no1, "courier": "Courier A", "trackingNumber": "WB" + SUFFIX},
                           files={"pickupReceipt": ("pickup.png", PNG, "image/png")})
    check("6. the admin ships the order with a pickup receipt photo", status in (200, 201) and body["shipment"]["hasPickupReceipt"], (status, body))
    sid = body["shipment"]["id"]
    check("6. order.shipped -> the payment knows courier and tracking number", wait_for(payment_with(no1, courier="Courier A", trackingNumber="WB" + SUFFIX)) is not None)
    check("6. order.shipped -> the shipped email arrives", wait_for(lambda: mail_to(email, no1, "WB" + SUFFIX)) is not None)

    status, body, _ = call("POST", ORDER + "/api/v1/order/admin/shipments/delivered", admin, {"shipmentIds": [sid]})
    check("7. the admin marks the parcel delivered", status == 200 and len(body["done"]) == 1, (status, body))
    check("7. order.delivered -> the payment becomes COLLECTED", wait_for(payment_with(no1, status="COLLECTED")) is not None)
    check("7. payment.collected -> the order shows paymentStatus COLLECTED", wait_for(order_with(no1, paymentStatus="COLLECTED")) is not None)

    status, rec, _ = call("POST", PAYMENT + "/api/v1/payment/admin/courier-receipts", admin,
                          fields={"courier": "Courier A", "receiptNo": "R-" + SUFFIX, "bankReference": "BANK-1", "receivedOn": time.strftime("%Y-%m-%d"),
                                  "amountReceived": f"{o1['total'] - 100:.2f}", "trackingNumbers": ["WB" + SUFFIX]},
                          files={"file": ("receipt.pdf", PDF, "application/pdf")})
    check("8. the admin enters the courier receipt (PDF in the private bucket)", status == 201 and rec["receipt"]["fees"] == 100, (status, rec))
    check("8. payment.succeeded -> the order shows paymentStatus PAID", wait_for(order_with(no1, paymentStatus="PAID")) is not None)
    if status == 201:
        status, content, _ = call("GET", PAYMENT + f"/api/v1/payment/admin/courier-receipts/{rec['receipt']['id']}/file", admin, raw=True)
        check("8. the receipt file comes back unchanged", status == 200 and content == PDF, status)

    # 9. cancel and return
    o2 = place(2)
    no2 = o2["orderNo"]
    wait_for(payment_with(no2, status="PENDING"))
    status, body, _ = call("POST", ORDER + f"/api/v1/order/orders/{no2}/cancel", customer)
    check("9. the customer cancels an order before shipping", status == 200, (status, body))
    check("9. order.cancelled -> the payment becomes CANCELLED", wait_for(payment_with(no2, status="CANCELLED")) is not None)
    check("9. payment.cancelled -> the order shows paymentStatus CANCELLED", wait_for(order_with(no2, paymentStatus="CANCELLED")) is not None)
    check("9. order.cancelled -> the cancelled email arrives", wait_for(lambda: mail_to(email, no2, "cancelled")) is not None)

    o3 = place(1)
    no3 = o3["orderNo"]
    wait_for(payment_with(no3, status="PENDING"))
    status, body, _ = call("POST", ORDER + "/api/v1/order/admin/shipments", admin, fields={"orderNo": no3, "courier": "Courier B", "trackingNumber": "XY" + SUFFIX})
    sid3 = body["shipment"]["id"] if status in (200, 201) else None
    status, body, _ = call("POST", ORDER + "/api/v1/order/admin/shipments/returned", admin, {"shipmentIds": [sid3], "reason": "REFUSED"})
    check("9. the admin marks a parcel returned", status == 200 and len(body["done"]) == 1, (status, body))
    check("9. order.returned -> the payment becomes CANCELLED", wait_for(payment_with(no3, status="CANCELLED")) is not None)
    status, body, _ = call("GET", PRODUCT + f"/api/v1/product/admin/products/{pid}", admin)
    check("9. stock: 5 - 1 (delivered) = 4 (the cancel and the return gave their parts back)", body.get("stockQty") == 4, body.get("stockQty"))

    # 10. who may call what
    for label, url in (("user admin list", USER + "/api/v1/user/admin/users"),
                       ("order admin list", ORDER + "/api/v1/order/admin/orders"),
                       ("payment admin list", PAYMENT + "/api/v1/payment/admin/payments"),
                       ("product admin list", PRODUCT + "/api/v1/product/admin/products")):
        s1, _, _ = call("GET", url)
        s2, b2, _ = call("GET", url, customer)
        s3, _, _ = call("GET", url, admin)
        check(f"10. {label}: no login 401, customer 403 with the shared error JSON, admin 200",
              s1 == 401 and s2 == 403 and isinstance(b2, dict) and b2.get("code") == "ACCESS_DENIED" and s3 == 200, (s1, s2, s3))
    status, body, _ = call("GET", ORDER + f"/api/v1/order/orders/{no1}", None)
    check("10. an order cannot be read without login", status == 401, status)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a crash is a failure, with a clear message
        print(f"\nThe smoke test stopped: {exc!r}")
        failures.append("crash")
    print(f"\n{checks - len([f for f in failures if f != 'crash'])}/{checks} checks passed")
    if failures:
        print("Failed:", "; ".join(failures))
    sys.exit(1 if failures else 0)
