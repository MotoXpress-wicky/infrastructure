# Checkout (cash on delivery)

All **Planned**. Numbers are the order of steps. `->>` call, `-->>` answer, `--)` event.

## 1. Place an order

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant O as order-service
    participant P as product-service
    participant R as RabbitMQ
    participant Pay as payment-service
    participant N as notification-service

    B->>O: POST /api/v1/order/orders (lines, address, phone)
    O->>O: logged in? lines not empty? quantities above 0?
    O->>O: make order number MX-10238
    O->>P: POST /internal/v1/product/reservations (MX-10238, lines)
    alt enough stock
        P->>P: lock rows, take stock, save reservation
        P-->>O: 200 real price of each line
        O->>O: total = lines + delivery fee
        O->>O: save order: NOT_SHIPPED, payment PENDING
        O--)R: order.placed (after commit)
        O-->>B: 201 order number, cash to pay
        B->>B: empty the cart, show "thank you"
        R--)Pay: order.placed
        Pay->>Pay: create payment PAY-5018: COD, PENDING
        R--)N: order.placed
        N->>N: email and push "order received"
    else not enough stock
        P-->>O: 409 OUT_OF_STOCK (which part, how many left)
        O-->>B: 409 OUT_OF_STOCK, nothing saved
    end
```

Points to notice:
- The price comes from product-service (step 6), never from the browser.
- If saving the order fails after step 6, order-service calls
  `DELETE /internal/v1/product/reservations/MX-10238` to give the stock back.
- The payment is created by the **event** (step 13). order-service does not wait for it.

## 2. Customer cancels before shipping

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant O as order-service
    participant P as product-service
    participant R as RabbitMQ
    participant Pay as payment-service

    B->>O: POST /api/v1/order/orders/MX-10238/cancel
    O->>O: your order? still NOT_SHIPPED?
    O->>P: DELETE /internal/v1/product/reservations/MX-10238
    P-->>O: 204 stock back
    O->>O: shipment_status CANCELLED
    O--)R: order.cancelled
    O-->>B: 200
    R--)Pay: order.cancelled
    Pay->>Pay: PAY-5018 PENDING to CANCELLED
    Pay--)R: payment.cancelled
    R--)O: payment.cancelled
    O->>O: payment_status copy CANCELLED
```

An admin cancels the same way from the Orders page (`/api/v1/order/admin/orders/{orderNo}/cancel`).
If product-service is down in step 3, the cancel fails and nothing changes. Try again.
