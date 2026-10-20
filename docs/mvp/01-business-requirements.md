# Business requirements (MVP)

**MVP** = Minimum Viable Product: the smallest version that real customers can use to buy parts.

## 1. The business in one paragraph

motoXpress is a website that sells **motorbike parts** in **Sri Lanka**, focused on
**Japanese bikes** (Honda, Yamaha, Suzuki, Kawasaki). Many are imported, so owners often
do not know which part fits. The site makes it easy: pick your bike, see the parts that fit.
Anyone can browse. A customer logs in to buy and pays **cash on delivery**.
The shop packs the parcel and gives it to a **courier company**. The courier delivers it,
collects the cash, and later pays the shop. Admins run the catalog, stock, shipments and
cash from couriers. Customers get **email and push** updates. Prices are in LKR.

## 2. Who is involved

| Actor | Who | Does |
|---|---|---|
| Visitor | Anyone, not logged in | Browses and searches parts |
| Customer | Registered user (`ROLE_USER`) | Buys, follows orders, cancels before shipping |
| Admin | User with `ROLE_ADMIN` | Catalog, stock, orders, shipments, payments, courier receipts, users |
| Courier company | Outside business, **no system link in the MVP** | Takes the parcel, gives a pickup receipt with a tracking number, delivers, collects cash, pays the shop later with a receipt |
| Outside systems | Google, Turnstile, email server, Firebase | Login, CAPTCHA, email, push |

## 3. How a part is described

> Bike: **Honda XR 250** · Part number: **123HG** · Part name: **Sprocket** · Category: **Chains and Sprockets**

| Field | Example | Rule |
|---|---|---|
| Part number | `123HG` | Required, unique, searchable |
| Part name | Sprocket | Required |
| Category | Chains and Sprockets | Required, exactly one; admins create categories |
| Fits these bikes | Honda XR 250, Honda XR 250 Baja | Zero or more bike models |
| Universal | yes / no | Yes = fits almost any bike (engine oil); no bike list needed |
| Part brand | Honda Genuine, DID, NGK | Optional; who made the part |
| Condition | New / Used | Default New |
| Price | 4,500.00 LKR | Required, above 0 |
| Stock | 12 | Whole number, never below 0 |
| Photos | 1 to 5 | Optional, strongly advised |

A **bike model** belongs to a **bike brand**: Honda → XR 250 (1996–2007, 250 cc). Years and engine size are optional.

## 4. How cash on delivery works

1. The customer orders. The order says "pay 9,500.00 LKR in cash".
2. The admin packs it, prints a packing slip, hands it to the courier, and gets a **pickup receipt** with a **tracking number**.
3. The admin creates the **shipment** in the system (courier + tracking number).
4. The courier delivers and takes the cash, or brings the parcel back (**returned**).
5. The admin marks it delivered or returned, from the courier's portal, a call, or a message.
6. Later the courier pays the shop, with a **courier receipt** listing tracking numbers.
7. The admin types that receipt into the system and uploads the PDF. The payments become **Paid**.

Only step 7 proves the money arrived.

## 5. User stories

**Must** = needed for the MVP. **Should** = add if time allows.

### Customer

| Id | Story | Priority | Status |
|---|---|---|---|
| C1 | Register, log in, log out, Google login, reset my password | Must | Built |
| C2 | Choose my bike (brand → model) and see only the parts that fit | Must | Planned |
| C3 | Browse parts by category | Must | Planned |
| C4 | Search by part number or name | Must | Planned |
| C5 | See one part: photos, price, stock, which bikes it fits | Must | Planned |
| C6 | Add parts to a cart, change quantities | Must | Planned |
| C7 | Check out with address and phone, pay cash on delivery | Must | Planned |
| C8 | See my orders, their status, and the courier and tracking number | Must | Planned |
| C9 | Cancel my order before it ships | Must | Planned |
| C10 | Press "I received it" | Should | Planned |
| C11 | Get emails: welcome, password reset, password changed | Must | Partly built |
| C12 | Get email **and push**: order placed, shipped (with tracking number), delivered, returned, cancelled | Must | Planned |
| C13 | Allow or refuse push notifications in my browser | Must | Planned |
| C14 | Upload a profile picture | Should | Planned |

### Admin

| Id | Story | Priority | Status |
|---|---|---|---|
| A1 | Log in to the admin site | Must | Planned (login is built) |
| A2 | Create, edit, hide bike brands and bike models | Must | Planned |
| A3 | Create, edit, hide categories | Must | Planned |
| A4 | Add a part with number, name, category, fitting bikes, price, stock, photos | Must | Planned |
| A5 | Edit a part, change its price, hide it | Must | Planned |
| A6 | Add or remove stock with a reason; see stock history | Must | Planned |
| A7 | See all orders with shipment status and payment status | Must | Planned |
| A8 | Print a packing slip | Should | Planned |
| A9 | Create a shipment: courier, tracking number, optional photo of the pickup receipt | Must | Planned |
| A10 | Mark parcels delivered or returned, one or many at once | Must | Planned |
| A11 | Cancel an order before it ships | Must | Planned |
| A12 | See all payments and their status | Must | Planned |
| A13 | Enter a courier receipt with its PDF and mark its payments paid | Must | Planned |
| A14 | See "overdue cash": delivered parcels the courier has not paid for after N days | Must | Planned |
| A15 | See users, lock and unlock | Should | Planned |
| A16 | Make another user an admin, with an audit log | Should | Planned |

## 6. Business rules

| Id | Rule |
|---|---|
| BR1 | Browsing is public. Buying needs a login. |
| BR2 | A part number is unique. |
| BR3 | Catalog items are hidden, never deleted. |
| BR4 | A category or bike model cannot be hidden while active parts use it. |
| BR5 | You cannot order more than the stock. Stock is reserved when the order is placed. |
| BR6 | Reserved stock comes back when the order is cancelled or the parcel is returned. |
| BR7 | The order keeps a copy of each part's name, number and price at buying time. |
| BR8 | One flat delivery fee for the whole country, set in config. |
| BR9 | An order can be cancelled only before it is shipped. |
| BR10 | One order has one shipment and one payment in the MVP. |
| BR11 | A tracking number can be used by only one shipment of the same courier. |
| BR12 | A payment becomes **Collected** when the parcel is delivered, **Paid** only through a courier receipt, **Cancelled** when the order is cancelled or returned. |
| BR13 | A courier receipt can only include payments of the same courier that are Collected. |
| BR14 | A payment is "overdue" when it has been Collected for more than N days (N in config, default 14). |
| BR15 | Stock changes and money changes record who did them and when. |
| BR16 | Only admins change the catalog, stock, shipments and payments. A customer may only cancel their own order. |

## 7. Not in the MVP

| Left out | Why |
|---|---|
| Card payments, refunds | Cash only for now (M2) |
| Recommendations | Not needed to sell parts |
| Rider app, courier API | Couriers deliver; the admin updates by hand (M6) |
| Customer returns after delivery | Needs a returns process |
| SMS | No provider chosen (decision 17) |
| Discounts, reviews, wishlist, guest checkout | Later |
| Sinhala and Tamil | English first |
| Staging and production | Added later from the same codebase (M11) |

## 8. Quality needs

| Need | Target |
|---|---|
| Security | Hashed passwords; HttpOnly cookies; CAPTCHA and rate limits; no secrets in git |
| Errors | One error JSON shape in every service |
| Logs | Every log line has the request's trace id |
| Mobile | The customer site works well on a phone |
| Data | Each service has its own database and DB user |
| Proof | Every courier receipt has its PDF or photo stored |
| Tests | Unit tests and controller tests in every service |
