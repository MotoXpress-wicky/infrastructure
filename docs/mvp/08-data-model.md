# Data model (MVP)

One section per database. Each service owns one database (decision 2).
There are **no foreign keys between databases**: `user_id` in `order_db` is just a copied number.

`PK` primary key · `FK` foreign key (same database) · `UK` unique ·
`decimal` = money: `numeric(12,2)` in SQL, `BigDecimal` in Java.
These diagrams are the plan for the **Flyway** SQL files.

## user_db

Owner: user-service. The first three tables are **Built**.

```mermaid
erDiagram
    USERS ||--o{ REFRESH_TOKENS : "has"
    USERS ||--o{ PASSWORD_RESET_TOKEN : "has"
    USERS ||--o{ ADMIN_AUDIT_LOG : "is target of"

    USERS {
        bigint id PK
        varchar name
        varchar email UK
        varchar password "empty for Google users"
        varchar roles "ROLE_USER, ROLE_ADMIN, ROLE_DEFAULT"
        varchar auth_provider "LOCAL or GOOGLE"
        boolean locked
    }
    REFRESH_TOKENS {
        bigint id PK
        varchar token_hash UK "never the raw token"
        bigint user_id FK
        timestamp expires_at
        timestamp revoked_at
    }
    PASSWORD_RESET_TOKEN {
        bigint id PK
        varchar token_hash UK
        bigint user_id FK
        timestamp expires_at
        timestamp used_at
        timestamp created_at
    }
    ADMIN_AUDIT_LOG {
        bigint id PK
        bigint actor_user_id "the admin"
        bigint target_user_id FK
        varchar action "BOOTSTRAP, PROMOTE, LOCK, UNLOCK"
        timestamp created_at
    }
```

`ADMIN_AUDIT_LOG` is **Planned**. When writing Flyway, check the SQL that Hibernate creates
today for `User.roles` (a `List<Role>`) and copy that shape.

## product_db

Owner: product-service. **Planned**.

```mermaid
erDiagram
    BRANDS ||--o{ BIKE_MODELS : "has"
    CATEGORIES ||--o{ PRODUCTS : "groups"
    PRODUCTS ||--o{ PRODUCT_FITMENTS : "fits"
    BIKE_MODELS ||--o{ PRODUCT_FITMENTS : "is fitted by"
    PRODUCTS ||--o{ PRODUCT_IMAGES : "has"
    PRODUCTS ||--o{ STOCK_RESERVATIONS : "is reserved by"
    PRODUCTS ||--o{ STOCK_MOVEMENTS : "has history"

    BRANDS {
        bigint id PK
        varchar name UK "Honda"
        boolean active
    }
    BIKE_MODELS {
        bigint id PK
        bigint brand_id FK
        varchar name "XR 250"
        int year_from "optional"
        int year_to "optional"
        int engine_cc "optional"
        boolean active
    }
    CATEGORIES {
        bigint id PK
        varchar name UK "Chains and Sprockets"
        boolean active
    }
    PRODUCTS {
        bigint id PK
        varchar part_number UK "123HG"
        varchar name "Sprocket"
        text description
        bigint category_id FK
        varchar part_brand "optional"
        varchar part_condition "NEW or USED"
        decimal price
        int stock_qty "never below 0"
        boolean universal_fit
        boolean active
        int version "optimistic lock"
        timestamp created_at
        timestamp updated_at
    }
    PRODUCT_FITMENTS {
        bigint product_id PK, FK
        bigint bike_model_id PK, FK
    }
    PRODUCT_IMAGES {
        bigint id PK
        bigint product_id FK
        varchar file_name
        int sort_order
    }
    STOCK_RESERVATIONS {
        bigint id PK
        varchar order_no
        bigint product_id FK
        int quantity
        varchar status "RESERVED or RELEASED"
        timestamp created_at
        timestamp released_at
    }
    STOCK_MOVEMENTS {
        bigint id PK
        bigint product_id FK
        int change_qty "+20 or -2"
        varchar reason "INITIAL, RESTOCK, CORRECTION, ORDER_RESERVED, ORDER_RELEASED"
        varchar order_no "when an order caused it"
        bigint admin_user_id "when an admin caused it"
        timestamp created_at
    }
```

Extra unique rules: `bike_models` (`brand_id`, `name`, `year_from`); `stock_reservations` (`order_no`, `product_id`).

## order_db

Owner: order-service. **Planned**.

```mermaid
erDiagram
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    ORDERS ||--o| SHIPMENTS : "is sent as"

    ORDERS {
        bigint id PK
        varchar order_no UK "MX-10238"
        bigint user_id "copied from user-service"
        varchar customer_name "copy"
        varchar customer_email "copy"
        varchar phone
        varchar address_line
        varchar city
        varchar district
        varchar payment_method "COD"
        varchar shipment_status "NOT_SHIPPED, IN_TRANSIT, DELIVERED, RETURNED, CANCELLED"
        varchar payment_status "copy: PENDING, COLLECTED, PAID, CANCELLED"
        decimal items_total
        decimal delivery_fee
        decimal total
        varchar currency "LKR"
        varchar cancelled_by "CUSTOMER or ADMIN"
        timestamp customer_confirmed_at "I received it"
        timestamp created_at
        timestamp cancelled_at
        int version "optimistic lock"
    }
    ORDER_ITEMS {
        bigint id PK
        bigint order_id FK
        bigint product_id "copied from product-service"
        varchar part_number "copy"
        varchar product_name "copy"
        decimal unit_price "price at buying time"
        int quantity
        decimal line_total
    }
    SHIPMENTS {
        bigint id PK
        bigint order_id FK, UK "one per order in the MVP"
        varchar courier "Courier A"
        varchar tracking_number "WB55310"
        varchar status "IN_TRANSIT, DELIVERED, RETURNED"
        varchar return_reason "REFUSED, NOT_REACHABLE, WRONG_ADDRESS, OTHER"
        varchar pickup_receipt_file "optional photo"
        bigint created_by "admin user id"
        timestamp shipped_at
        timestamp delivered_at
        timestamp returned_at
    }
    PROCESSED_MESSAGES {
        uuid message_id PK
        timestamp processed_at
    }
```

- `shipments`: (`courier`, `tracking_number`) is unique (BR11).
- `order_id` is unique only in the MVP. Remove that rule later to allow split deliveries.
- `PROCESSED_MESSAGES` remembers handled event ids. Insert it in the **same** transaction as the change.

## payment_db

Owner: payment-service. **Planned**. No word "order": it says `reference`.

```mermaid
erDiagram
    COURIER_RECEIPTS ||--o{ PAYMENTS : "settles"

    PAYMENTS {
        uuid id PK
        varchar payment_no UK "PAY-5018"
        varchar reference UK "MX-10238, one payment per reference in the MVP"
        varchar method "COD"
        decimal amount
        varchar currency "LKR"
        varchar status "PENDING, COLLECTED, PAID, CANCELLED"
        varchar courier "set on order.shipped"
        varchar tracking_number "set on order.shipped"
        uuid courier_receipt_id FK "set when PAID"
        timestamp created_at
        timestamp collected_at
        timestamp paid_at
        timestamp cancelled_at
        int version "optimistic lock"
    }
    COURIER_RECEIPTS {
        uuid id PK
        varchar courier
        varchar receipt_no "R-41"
        varchar bank_reference
        date received_on
        decimal collected_total "sum of its payments"
        decimal fees "collected minus received"
        decimal amount_received
        varchar file_name "PDF or photo, required"
        bigint created_by "admin user id"
        timestamp created_at
    }
    PROCESSED_MESSAGES {
        uuid message_id PK
        timestamp processed_at
    }
```

- `courier_receipts`: (`courier`, `receipt_no`) is unique, so the same receipt cannot be entered twice.
- `payments`: index on (`courier`, `tracking_number`) to match receipt lines fast.
- Card payments later: drop the unique rule on `reference` (a failed try, then a good one).

## notification_db

Owner: notification-service. **Planned**.

```mermaid
erDiagram
    PUSH_DEVICES {
        bigint id PK
        bigint user_id "copied from user-service"
        varchar token UK "Firebase device token"
        timestamp created_at
        timestamp last_used_at
    }
    SENT_NOTIFICATIONS {
        bigint id PK
        uuid message_id "the event's messageId"
        varchar channel "EMAIL or PUSH"
        varchar event_name "order.shipped"
        varchar recipient "email address, or user id for push"
        varchar template
        varchar status "SENT or FAILED"
        varchar error
        timestamp created_at
    }
```

`sent_notifications`: (`message_id`, `channel`) is unique. That is the duplicate check.

## Databases on the PostgreSQL server

| Database | DB user | In `01-create-databases.sh` today? |
|---|---|---|
| `user_db` | `user_service` | Yes |
| `product_db` | `product_service` | Yes |
| `order_db` | `order_service` | Yes |
| `notification_db` | `notification_service` | Yes |
| `payment_db` | `payment_service` | **No — must be added** |
| `suggestion_db` | `suggestion_service` | Yes — **not needed**, remove |
