# Shipping and cash from the courier

All **Planned**. The allowed status moves are in [09-state-diagrams.md](../09-state-diagrams.md).

## 1. Create a shipment

The admin has packed the parcel, handed it to the courier, and has the pickup receipt with
tracking number WB55310.

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant O as order-service
    participant R as RabbitMQ
    participant Pay as payment-service
    participant N as notification-service

    A->>O: POST /api/v1/order/admin/shipments (MX-10238, Courier A, WB55310, photo)
    O->>O: order NOT_SHIPPED? no shipment yet? WB55310 not used before?
    alt allowed
        O->>O: save shipment IN_TRANSIT, order shipment_status IN_TRANSIT
        O--)R: order.shipped (courier, tracking number)
        O-->>A: 201
        R--)Pay: order.shipped
        Pay->>Pay: save Courier A and WB55310 on PAY-5018
        R--)N: order.shipped
        N->>N: email and push "on its way, tracking WB55310"
    else not allowed
        O-->>A: 409 INVALID_ORDER_STATUS or TRACKING_NUMBER_TAKEN
    end
```

## 2. Mark delivered (the courier has the cash)

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant O as order-service
    participant R as RabbitMQ
    participant Pay as payment-service
    participant N as notification-service

    A->>O: POST /api/v1/order/admin/shipments/delivered (WB55310, WB55311, ...)
    O->>O: each one IN_TRANSIT? then DELIVERED
    O--)R: order.delivered (one per order)
    O-->>A: 200
    R--)Pay: order.delivered
    Pay->>Pay: PAY-5018 PENDING to COLLECTED
    Pay--)R: payment.collected
    R--)O: payment.collected
    O->>O: payment_status copy COLLECTED
    R--)N: order.delivered
    N->>N: email and push "delivered"
```

## 3. Mark returned (the courier brought it back)

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant O as order-service
    participant P as product-service
    participant R as RabbitMQ
    participant Pay as payment-service

    A->>O: POST /api/v1/order/admin/shipments/returned (WB55310, reason REFUSED)
    O->>O: IN_TRANSIT? then RETURNED
    O->>P: DELETE /internal/v1/product/reservations/MX-10238
    P-->>O: 204 stock back
    O--)R: order.returned (reason)
    O-->>A: 200
    R--)Pay: order.returned
    Pay->>Pay: PAY-5018 PENDING to CANCELLED
    Pay--)R: payment.cancelled
    R--)O: payment.cancelled
    O->>O: payment_status copy CANCELLED
```

Return reasons: `REFUSED`, `NOT_REACHABLE`, `WRONG_ADDRESS`, `OTHER`.
If the part came back damaged, the admin removes it with a stock adjustment.

## 4. The courier pays: enter a courier receipt

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant Pay as payment-service
    participant R as RabbitMQ
    participant O as order-service

    A->>Pay: GET /api/v1/payment/admin/payments?courier=A&status=COLLECTED
    Pay-->>A: Collected parcels of Courier A with tracking numbers
    A->>Pay: POST /api/v1/payment/admin/courier-receipts (R-41, date, bank ref, 11,950.00, PDF, tracking numbers)
    Pay->>Pay: every tracking number found, Courier A, COLLECTED?
    alt all good
        Pay->>Pay: one transaction: save receipt + file, payments PAID
        Pay--)R: payment.succeeded (one per payment)
        Pay-->>A: 201 collected 12,600.00, fees 650.00
        R--)O: payment.succeeded
        O->>O: payment_status copy PAID
    else a problem
        Pay-->>A: 409 with the list: unknown, other courier, or not COLLECTED yet
    end
```

If a parcel on the receipt is still `PENDING`, the admin has not marked it delivered yet.
The answer says "mark WB55312 delivered first". Money is never accepted for a parcel that
the system thinks is still on the road.

## 5. Customer presses "I received it"

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant O as order-service

    B->>O: POST /api/v1/order/orders/MX-10238/received
    O->>O: your order? IN_TRANSIT or DELIVERED?
    O->>O: save customer_confirmed_at (no status change)
    O-->>B: 200
```

The admin sees "customer confirmed" on the order. It is evidence only (M21).
