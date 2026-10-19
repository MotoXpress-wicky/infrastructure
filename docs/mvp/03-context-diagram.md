# Context diagram (C4 level 1) — MVP

motoXpress as one box, the people around it, and the outside systems it calls.

```mermaid
flowchart LR
    visitor([Visitor<br/>browses parts])
    customer([Customer<br/>buys, pays cash])
    admin([Admin<br/>runs the shop])
    courier([Courier company<br/>delivers, collects cash])

    system["motoXpress<br/>motorbike part shop"]

    google[["Google<br/>social login"]]
    turnstile[["Turnstile<br/>CAPTCHA"]]
    email[["Email server<br/>Mailpit in dev"]]
    fcm[["Firebase Cloud Messaging<br/>push"]]

    visitor -->|browse, search| system
    customer -->|order, track, cancel| system
    admin -->|catalog, shipments, cash| system
    admin <-.->|"parcels, tracking numbers,<br/>cash and receipts (no system link)"| courier
    courier -.->|delivers, collects cash| customer

    system -->|sign in| google
    system -->|check CAPTCHA| turnstile
    system -->|emails| email
    system -->|push messages| fcm
    fcm -.->|notification on the device| customer
```

## Outside systems

| System | Used for | Called by |
|---|---|---|
| Google | "Continue with Google" | user-service (built) |
| Turnstile | CAPTCHA on register and forgot password | user-service (built) |
| Email server | All emails. Mailpit (a fake inbox) in dev. | notification-service |
| Firebase Cloud Messaging | Push messages to the customer's browser | notification-service |

## The courier is outside, and not connected

In the MVP the courier company has **no link** to our system. The admin talks to the courier
and types what they learn into the admin site: tracking numbers, delivered or returned, and
courier receipts. A courier API can replace the typing later (decision M6).

## Inside, not outside

PostgreSQL, Redis, RabbitMQ and Nginx are inside motoXpress: we run them.
See the [container diagram](04-container-diagram.md).
