# Browse, search, cart

All **Planned**. No login needed for any step here (BR1).

## 1. Find parts for my bike

```mermaid
sequenceDiagram
    autonumber
    actor V as Visitor
    participant B as Browser (users-ui)
    participant P as product-service

    V->>B: open the site
    B->>P: GET /api/v1/product/brands
    P-->>B: Honda, Yamaha, Suzuki, Kawasaki
    V->>B: pick Honda
    B->>P: GET /api/v1/product/brands/{brandId}/models
    P-->>B: XR 250, CB 125, ...
    V->>B: pick XR 250
    B->>P: GET /api/v1/product/products?bikeModelId=...
    P->>P: active parts that fit this model, plus universal parts
    P-->>B: one page of parts (number, name, price, in stock?, first photo)
```

The UI keeps the chosen bike in the browser, so every later list is filtered for that bike.

## 2. Search by part number or name

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant P as product-service

    B->>P: GET /api/v1/product/products?q=123HG
    P->>P: exact part number first, then names that contain the words
    P-->>B: matching active parts
```

## 3. Open one part

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant P as product-service
    participant S as Object storage (bucket product-media)

    B->>P: GET /api/v1/product/products/{id}
    P-->>B: number, name, category, part brand, condition, price, stock, fitting bikes, photo URLs (MEDIA_BASE_URL + key)
    B->>S: GET /media/products/42/sprocket-1.jpg (one per photo, via Nginx)
    S-->>B: image
```

A hidden part answers `404`. Old orders still show it from their own copy (BR3, BR7).

## 4. Add to cart

```mermaid
sequenceDiagram
    autonumber
    actor V as Visitor
    participant B as Browser (cartStore)

    V->>B: "Add to cart", quantity 2
    B->>B: add or update the line (part id, quantity, name and price to show)
    B->>B: save the cart in the browser
```

No server call. The cart lives only in this browser (decision 37).
Stock is **not** reserved yet. That happens at checkout.
