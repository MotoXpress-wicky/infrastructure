# Push notifications

All **Planned**. Push uses Firebase Cloud Messaging (M9).

## 1. The customer allows push in this browser

```mermaid
sequenceDiagram
    autonumber
    actor C as Customer
    participant B as Browser (users-ui)
    participant F as Firebase
    participant N as notification-service

    B->>C: "Allow notifications?" (after login)
    C->>B: Allow
    B->>F: register this browser (Firebase JS SDK)
    F-->>B: device token
    B->>N: POST /api/v1/notification/push-devices (token)
    N->>N: logged in? save token for this user id
    N-->>B: 201
```

If the customer says "Block", nothing is saved. They still get emails.
On logout, the browser calls `DELETE /api/v1/notification/push-devices/{token}`.

## 2. An event becomes an email and a push

```mermaid
sequenceDiagram
    autonumber
    participant R as RabbitMQ
    participant N as notification-service
    participant M as Email server
    participant F as Firebase
    actor C as Customer device

    R--)N: order.shipped on notification.email
    N->>N: messageId new? fill the order-shipped email
    N->>M: send to the email in the event
    R--)N: order.shipped on notification.push
    N->>N: messageId new? find this user's devices
    loop each device token
        N->>F: send title and text
        alt token still valid
            F--)C: notification appears, even if the site is closed
        else token no longer valid
            F-->>N: unregistered
            N->>N: delete that device
        end
    end
```

The same event arrives twice, once per queue. Email and push are sent independently: if one
fails and is retried, the other is not sent again.
