# Admin: users and roles

All **Planned**. Based on decision 8: the first admin by bootstrap, the next ones by promotion, with an audit log.

## 1. The first admin (bootstrap)

```mermaid
sequenceDiagram
    autonumber
    actor Y as You
    participant U as user-service
    participant DB as user_db

    Y->>U: register a normal account with your email (website)
    Y->>Y: put that email in user-service .env as the bootstrap admin email
    Y->>U: restart user-service
    U->>DB: is there any user with ROLE_ADMIN?
    alt no admin yet
        U->>DB: find the user with the bootstrap email
        U->>DB: add ROLE_ADMIN, write audit log "BOOTSTRAP"
    else an admin already exists
        U->>U: do nothing
    end
```

No password is ever written in config or git. The account is created normally first.
If the email is not found, user-service logs a warning and starts anyway.

## 2. An admin makes another user an admin

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant U as user-service
    participant DB as user_db

    A->>U: POST /api/v1/user/admin/users/{id}/promote
    U->>U: caller has ROLE_ADMIN?
    U->>DB: add ROLE_ADMIN to that user
    U->>DB: audit log: who, to whom, PROMOTE, when
    U-->>A: 200
```

The new admin's role shows up in their **next** access token. Their current token
still says "not admin" for up to 15 minutes (the token life), or until they log in again.

## 3. Lock a user

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant U as user-service
    participant DB as user_db

    A->>U: POST /api/v1/user/admin/users/{id}/lock
    U->>U: caller is admin? not locking yourself?
    U->>DB: locked true, revoke all their refresh tokens
    U->>DB: audit log: LOCK
    U-->>A: 200
```

A locked user cannot log in or refresh (Built: login already refuses locked accounts).
Their current access token still works until it expires (up to 15 minutes).

## Cookies and the two sites

Browsers keep cookies per **host name**. `localhost` (customer site) and `admin.localhost`
(admin site) are different host names, so they have **separate** cookies (decision M10).
An admin logs in on the admin site with email and password. Being logged in as a customer on
`localhost` does not log you in on `admin.localhost`. Every admin call still needs `ROLE_ADMIN`.
