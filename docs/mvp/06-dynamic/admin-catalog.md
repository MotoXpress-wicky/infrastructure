# Admin: catalog and stock

All **Planned**. Every call needs `ROLE_ADMIN`. product-service checks it on every request.

## 1. Set up the catalog: category, bike brand, bike model

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant P as product-service

    A->>P: POST /api/v1/product/admin/categories (name "Chains and Sprockets")
    P->>P: name not used yet? save
    P-->>A: 201 category
    A->>P: POST /api/v1/product/admin/brands (name "Honda")
    P-->>A: 201 brand
    A->>P: POST /api/v1/product/admin/brands/{brandId}/models (XR 250, 1996, 2007, 250 cc)
    P->>P: same model name and years not used for this brand? save
    P-->>A: 201 bike model
```

## 2. Add a part, with fitment and photos

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant P as product-service
    participant S as Object storage (bucket product-media)

    A->>P: POST /api/v1/product/admin/products (123HG, Sprocket, category, price, start stock, bike model ids)
    P->>P: part number unique? category and models active? price above 0?
    P->>P: save part, save fitment rows, write stock change "initial stock"
    P-->>A: 201 part id
    loop each photo, up to 5
        A->>P: POST /api/v1/product/admin/products/{id}/photos (file)
        P->>P: image type? size under the limit?
        P->>S: PUT products/{id}/photo-1.jpg (S3 API)
        P->>P: save only the key
        P-->>A: 201 photo URL (MEDIA_BASE_URL + key)
    end
```

## 3. Add or remove stock

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant P as product-service

    A->>P: POST /api/v1/product/admin/products/{id}/stock (change +20, reason "new delivery")
    P->>P: lock the part row
    alt new stock is 0 or more
        P->>P: update stock, write stock change (who, +20, reason)
        P-->>A: 200 new stock
    else would go below 0
        P-->>A: 409 STOCK_BELOW_ZERO
    end
```

The lock in step 2 stops an admin change and a customer order from overwriting each other.

## 4. Hide a category that is still used

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant P as product-service

    A->>P: PATCH /api/v1/product/admin/categories/{id} (active false)
    P->>P: any active part in this category?
    alt yes
        P-->>A: 409 CATEGORY_IN_USE (how many parts)
    else no
        P->>P: active false
        P-->>A: 200
    end
```

Bike models follow the same rule (BR4).
