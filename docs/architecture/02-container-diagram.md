# Container diagram (C4 level 2)

This diagram opens the motoXpress system box from the context diagram.
It shows every separately running part: the gateway, the services, the
databases, and the outside systems.

Status: draft for review. Not final.



```mermaid
flowchart TB
    customer([Customer browser])
    admin([Admin browser])

    nginx["Nginx gateway"]

    subgraph userbox [user]
        user["user-service"]
        userdb[("user_db + Redis")]
    end

    subgraph productbox [product]
        product["product-service"]
        productdb[("product_db")]
    end

    subgraph orderbox [order]
        order["order-service"]
        orderdb[("order_db")]
    end

    subgraph paymentbox [payment]
        payment["payment-service"]
        paymentdb[("payment_db")]
    end

    subgraph notifbox [notification]
        notif["notification-service"]
    end

    subgraph recobox [recommendation]
        reco["recommendation-service"]
        recodb[("recommendation_db")]
    end

    onepay[["OnePay"]]
    acs[["ACS Email"]]
    google[["Google login"]]

    %% ---------- HTTP: solid line, caller waits ----------
    customer --> nginx
    admin --> nginx
    nginx --> user
    nginx --> product
    nginx --> order
    nginx --> payment
    nginx -->|show suggested items| reco

    user --> userdb
    product --> productdb
    order --> orderdb
    payment --> paymentdb
    reco --> recodb

    order -->|check stock and price| product
    order -->|start a payment| payment
    user -->|sign in| google
    payment -->|create and verify payment| onepay
    onepay -->|payment result webhook| payment
    notif -->|send the email| acs

    %% ---------- Events: dotted line, no waiting ----------
    payment -.->|"payment.succeeded<br/>payment.failed<br/>payment.refunded"| order

    user -.->|"user.registered<br/>user.password.reset<br/>user.password.changed"| notif

    order -.->|"order.placed<br/>order.paid<br/>order.shipped<br/>order.cancelled<br/>order.refund_requested<br/>order.refunded"| notif

    order -.->|"order.paid"| reco

    product -.->|"product.created<br/>product.updated<br/>product.deleted"| reco

    %% ---------- Cancellation & Refund Events ----------
    order -.->|"order.cancelled"| payment
```


## What each service does

| Service | Job | Domain-free? |
|---|---|---|
| **Nginx gateway** | Single entry point; routes requests to the correct service | — |
| **user-service** | Login, sign-up, tokens, user accounts | **Yes** |
| **product-service** | Products, categories, stock, vehicle fit | **No** |
| **order-service** | Checkout, orders, order status | **No** |
| **payment-service** | Talks to OnePay; records payments | **Yes** |
| **notification-service** | Sends email and push | **Yes** |
| **recommendation-service** | Generates product recommendations (Python, LightFM) | **Yes** |

Push messages need an outside push provider. It is not chosen yet, so it is not drawn.