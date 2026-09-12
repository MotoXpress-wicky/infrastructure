# Container diagram (C4 level 2)

This diagram opens the motoXpress system box from the context diagram.
It shows every separately running part: the gateway, the services, the
databases, and the outside systems.

Status: draft for review. Not final.

## How to read the arrows

- A solid arrow means HTTP. The caller sends a request and waits for the answer.
- A dotted arrow means an event. The sender does not wait for any answer.
- All events travel through RabbitMQ, our message broker. The broker box is not
  drawn, to keep the picture clear.
- Arrow labels use plain words. The exact event names used in the code are in
  the event legend below the diagram.

```mermaid
flowchart TB
    customer([Customer browser])
    admin([Admin browser])

    nginx["Nginx gateway<br/>one door for all requests"]

    subgraph userbox [user]
        user["user-service<br/>login and accounts"]
        userdb[("user_db + Redis")]
    end
    subgraph productbox [product]
        product["product-service<br/>products and stock"]
        productdb[("product_db")]
    end
    subgraph orderbox [order]
        order["order-service<br/>orders and checkout"]
        orderdb[("order_db")]
    end
    subgraph paymentbox [payment]
        payment["payment-service<br/>payments"]
        paymentdb[("payment_db")]
    end
    subgraph notifbox [notification]
        notif["notification-service<br/>sends messages"]
    end
    subgraph recobox [recommendation]
        reco["recommendation-service<br/>Python, LightFM"]
        recodb[("recommendation_db")]
    end

    onepay[["OnePay<br/>card payment gateway"]]
    acs[["ACS Email<br/>email sender"]]
    google[["Google<br/>social login"]]

    %% ---------- HTTP: solid line, caller waits ----------
    customer --> nginx
    admin --> nginx
    nginx --> user
    nginx --> product
    nginx --> order
    nginx --> payment

    user --> userdb
    product --> productdb
    order --> orderdb
    payment --> paymentdb
    reco --> recodb

    order -->|check stock and price| product
    order -->|start a payment| payment
    order -->|get suggested items| reco
    user -->|sign in with Google| google
    payment -->|create and verify payment| onepay
    onepay -->|payment result webhook| payment
    notif -->|send the email| acs

    %% ---------- events: dotted line, no waiting ----------
    payment -.->|payment result| order
    order -.->|send email to customer| notif
    user -.->|send email to customer| notif
    order -.->|paid order details| reco
    product -.->|product added or changed| reco

    %% ---------- legend ----------
    subgraph legend [Legend: shapes and arrows]
        direction LR
        L1[service] --- L2[("database")]
        L2 --- L3{{"broker: RabbitMQ"}}
        L3 --- L4[[outside system]]
        L5[A] -->|HTTP, caller waits| L6[B]
        L7[C] -.->|event, no waiting| L8[D]
    end
```

## Legend 1: what each running part does

| Service                    | Job                                                        | Domain-free? | Reason                                                                                             |
| -------------------------- | ---------------------------------------------------------- | ------------ | -------------------------------------------------------------------------------------------------- |
| **Nginx gateway**          | Single entry point; routes requests to the correct service | —            | Infrastructure component                                                                           |
| **user-service**           | Login, sign-up, tokens, user accounts                      | **Yes**      | Only handles accounts, authentication, roles, and tokens                                           |
| **product-service**        | Products, categories, stock, vehicle fit                   | **No**       | Product and vehicle-fit rules are core MotoXpress business logic                                   |
| **order-service**          | Checkout, orders, order status                             | **No**       | Checkout and order rules are core MotoXpress business logic                                        |
| **payment-service**        | Communicates with OnePay; records payments                 | **Yes**      | Handles amounts, payment references, and gateway communication without knowing what was purchased  |
| **notification-service**   | Sends email notifications                                  | **Yes**      | Only needs a message, recipient/address, and template information                                  |
| **recommendation-service** | Generates product recommendations                          | **Yes**      | Works with generic users, items, and interactions; recommendation logic is reusable across systems |


## Legend 2: what each event line means

The middle column is the real event name in the code. The picture uses the
plain words instead, so any reader can follow it.

| Plain words on the line | Event name in code | What it means |
|---|---|---|
| payment result | payment.succeeded / payment.failed | payment-service tells order-service if the card payment worked or not, so order-service can mark the order paid or unpaid. |
| send email to customer (from order) | notification.requested | order-service asks notification-service to email the customer, for example "your order is paid". |
| send email to customer (from user) | notification.requested | user-service asks notification-service to email the customer, for example a welcome email. |
| paid order details | interaction.recorded | order-service sends only successful, paid orders to recommendation-service, which stores them in its own table as purchase history. |
| product added or changed | item.changed | when a product is added or edited, product-service sends it to recommendation-service, which keeps its own small copy for making suggestions. |

