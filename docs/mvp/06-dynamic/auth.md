# Login and account flows

How to read: each number is one step, in time order. Solid arrow `->>` = HTTP call.
Dashed arrow `-->>` = the answer. Dotted open arrow `--)` = an event (no waiting).
**Built** steps exist in user-service today. **Planned** steps are marked.

## 1. Register

```mermaid
sequenceDiagram
    autonumber
    actor C as Customer
    participant B as Browser (users-ui)
    participant T as Turnstile
    participant U as user-service
    participant R as RabbitMQ
    participant N as notification-service

    C->>B: fills name, email, password
    B->>T: run the CAPTCHA widget
    T-->>B: captcha token
    B->>U: POST /api/v1/user/auth/register (via Nginx)
    U->>U: rate limit check (per IP)
    U->>T: is this captcha token valid?
    T-->>U: yes
    U->>U: email not taken? hash password, save user
    U--)R: user.registered (Planned)
    U-->>B: 200 "User registered successfully"
    R--)N: user.registered
    N->>N: send the welcome email (Planned)
```

Register does **not** log the user in. The UI sends them to the login page.

## 2. Log in

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant U as user-service
    participant DB as user_db

    B->>U: POST /api/v1/user/auth/login (email, password)
    U->>U: rate limit (per IP and per email)
    U->>DB: find user, check password hash, not locked?
    U->>DB: save a new refresh token (only its hash)
    U-->>B: 200 user JSON + Set-Cookie access_token (path /) + Set-Cookie refresh_token (path /api/v1/user/auth)
```

Both cookies are **HttpOnly**: JavaScript cannot read them, so a script injected into the
page cannot steal them. The browser sends them on its own.

## 3. Call another service while logged in

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant N as Nginx
    participant O as order-service

    B->>N: GET /api/v1/order/orders (cookie access_token goes along)
    N->>O: same request + X-Request-Id
    O->>O: check token signature with user-service public key (no call to user-service)
    alt token is good
        O-->>B: 200 my orders
    else token is old
        O-->>B: 401 code ACCESS_TOKEN_EXPIRED, refreshable true
    end
```

order-service never asks user-service "is this token OK?". The public key is enough (decision M9).
That is why one service can be down and the others still work.

## 4. Refresh an old access token

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (axios interceptor)
    participant U as user-service

    B->>U: any call → 401 ACCESS_TOKEN_EXPIRED, refreshable true
    B->>U: POST /api/v1/user/auth/refresh (refresh_token cookie)
    U->>U: token known, not expired, not used before?
    alt good
        U->>U: mark old refresh token used, make a new one (rotation)
        U-->>B: 200 + two new cookies
        B->>U: repeat the first call once
    else the old refresh token was used again
        U->>U: someone copied it: revoke every session of this user
        U-->>B: 401 REFRESH_TOKEN_REUSED + clear both cookies
        B->>B: clear the user, go to /login
    end
```

If ten calls fail at the same time, the interceptor sends **one** refresh, not ten (Built).

## 5. Google login

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant U as user-service
    participant G as Google

    B->>U: GET /oauth2/authorization/google (full page, via Nginx)
    U-->>B: redirect to Google
    B->>G: log in and agree
    G-->>B: redirect to /login/oauth2/code/google?code=...
    B->>U: GET /login/oauth2/code/google?code=...
    U->>G: swap the code for the user's identity
    G-->>U: email, name (signed id token)
    U->>U: find the user by email, or create one with provider GOOGLE
    U-->>B: Set-Cookie both tokens + redirect to http://localhost/
```

Open: behind Nginx, Spring must build the redirect address from Nginx's forwarded headers.
Test this in the first end-to-end run. The Google console must list
`http://localhost/login/oauth2/code/google` as an allowed redirect URI.

## 6. Forgot and reset password

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant U as user-service
    participant R as RabbitMQ
    participant N as notification-service

    B->>U: POST /api/v1/user/auth/forgot-password (email, captcha token)
    U->>U: captcha, rate limit (per IP and per email)
    opt the account exists
        U->>U: make a reset token, save only its hash, 30 minutes life
        U--)R: user.password.reset with the reset link (Planned)
        R--)N: user.password.reset
        N->>N: send the reset email
    end
    U-->>B: 200 same message every time
    B->>U: GET /api/v1/user/auth/reset-password/validate?token=...
    U-->>B: 204 good, or 400 INVALID_RESET_TOKEN
    B->>U: POST /api/v1/user/auth/reset-password (token, new password)
    U->>U: save new hash, mark token used
    U--)R: user.password.changed (Planned)
    U-->>B: 200 + clear access cookie, "please sign in"
```

The answer in step 7 is the same whether or not the email exists.
So nobody can use this page to find out who has an account.

Today (Built) user-service sends these two emails itself. In the MVP it publishes the events
instead, and notification-service sends them (decision M14).
