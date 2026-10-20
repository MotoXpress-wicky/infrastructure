# product-service — components (C4 level 3)

Job: the catalog (bike brands, bike models, categories, parts, fitment, photos) and stock.
Port 8081. Not domain-free: this is the heart of the shop. Everything here is **Planned**.

```mermaid
flowchart TB
    req([HTTP request from Nginx])
    orderSvc(["order-service"])

    subgraph svc [product-service]
        jwtf["JwtCheckFilter<br/>checks token with the public key"]
        catc["CatalogController<br/>public browse and search"]
        admcat["AdminCatalogController<br/>brands, bike models, categories"]
        admprod["AdminProductController<br/>parts, fitment, photos, stock"]
        intc["ReservationController<br/>internal: reserve, release"]

        catsvc["CatalogService<br/>brands, models, categories"]
        prodsvc["ProductService<br/>parts, fitment, search"]
        stock["StockService<br/>reserve, release, adjust"]
        files["ObjectStorageClient<br/>AWS S3 client"]
        repo["Repositories"]
    end

    db[("product_db")]
    folder[("object storage<br/>bucket product-media")]

    req --> jwtf
    jwtf --> catc
    jwtf --> admcat
    jwtf --> admprod
    orderSvc --> intc

    catc --> catsvc
    catc --> prodsvc
    admcat --> catsvc
    admprod --> prodsvc
    admprod --> stock
    admprod --> files
    intc --> stock

    files --> folder
    catsvc --> repo
    prodsvc --> repo
    stock --> repo
    repo --> db

    classDef planned stroke-dasharray: 5 5
    class jwtf,catc,admcat,admprod,intc,catsvc,prodsvc,stock,files,repo planned
```

## Parts

| Part | Job |
|---|---|
| JwtCheckFilter | Admin endpoints need `ROLE_ADMIN`. Public endpoints need no login. |
| CatalogController | Public: brands, models of a brand, categories, search parts, one part, photos |
| AdminCatalogController | Create, edit, hide brands, bike models, categories (BR3, BR4) |
| AdminProductController | Create, edit, hide parts; fitment; upload photos; adjust stock; stock history |
| ReservationController | **Internal** (`/internal/...`), only order-service calls it, Nginx never routes it |
| CatalogService | Example rule: cannot hide a category that active parts use |
| ProductService | Example rule: part number must be unique. Search by number, name, category, bike model. |
| StockService | Reserve for an order, release on cancel **or return**, admin adjustments. Every change is written to `stock_movements`. Locks the part row while changing stock. |
| ObjectStorageClient | Puts and deletes files in its own bucket `product-media` (public read) with the AWS SDK S3 client (M18). Saves only the object key. Address and keys come from `env/product-service.env`. |
| Repositories | `brands`, `bike_models`, `categories`, `products`, `product_fitments`, `product_images`, `stock_reservations`, `stock_movements` |

## Stock in one picture

```mermaid
flowchart LR
    a["stock_qty = 10"] -->|"MX-1 reserves 2"| b["stock_qty = 8<br/>reservation MX-1: 2"]
    b -->|"MX-1 cancelled or returned"| c["stock_qty = 10<br/>reservation RELEASED"]
    b -->|"MX-1 delivered"| d["stock_qty stays 8<br/>reservation stays RESERVED"]
```

Each reservation is saved with the order number, so releasing the same order twice does nothing
the second time (idempotent).

## Settings in `application.yaml`

File folder, max photo size, max photos per part (5), search page size, public key location.

Tables: [08-data-model.md](../08-data-model.md#product_db). Endpoints: [10-api-map.md](../10-api-map.md#product-service-8081).
