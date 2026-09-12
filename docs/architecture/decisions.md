# Architecture decisions

Each row is one decision and the reason for it.
Status: Accepted (final) or Proposed (may still change).
Note: how services talk to each other (events vs HTTP) is not decided yet,
so those decisions are not listed here.

| # | Decision | Reason | Status |
|---|---|---|---|
| 2 | One service = one job = one database; never read another service's tables | Clear ownership | Accepted |
| 3 | JWT signed with RS256: user-service signs, other services only verify | Only user-service can create tokens | Proposed |
| 4 | Local gateway: Nginx, routing only, no business logic | Smallest thing that works; one origin, so no CORS | Accepted |
| 6 | One PostgreSQL server, separate databases and separate DB users | Cheap; DB users stop cross-service access | Proposed |
| 7 | No admin-service; admins are users with ROLE_ADMIN in user-service | One login system; standard RBAC | Accepted |
| 8 | First admin by bootstrap; other admins promoted by an existing admin, with an audit log | No passwords in git; record of who did what | Proposed |
| 9 | infrastructure repo has local/, k8s/, terraform/ | Each folder has one job | Accepted |
| 10 | Production deploy with GitOps: CI builds an image, updates the tag in k8s/, ArgoCD deploys | Git is the single source of truth | Accepted |
| 11 | Kustomize with base + overlays for Kubernetes config | Plain YAML, built into kubectl | Proposed |
| 12 | API paths: /api/v1/<service>/... | One clear address pattern per service | Accepted |
| 13 | Local: Docker Compose runs only helpers; services and UIs run on the laptop; Nginx reaches them via host.docker.internal | Fast restarts and easy debugging | Accepted |
| 14 | Kubernetes is the last phase; practice with kind or minikube first | Managed clusters cost money every hour | Accepted |
| 15 | Cloud: Azure. Terraform uses the Azure provider | Chosen deployment target | Accepted |
| 16 | Email through SMTP only. Mailpit locally, ACS Email in production | Swap provider by config, no code change | Accepted |
| 17 | No SMS for now | Out of scope | Accepted |
| 18 | Payments: card through OnePay hosted checkout (sandbox), plus cash on delivery | Available in Sri Lanka; safe hosted checkout | Proposed |
| 19 | payment-service is domain-free and hides the gateway behind an interface | Reuse and easy gateway swap | Proposed |
| 20 | Build cash on delivery first, OnePay second | Finish the order flow without a gateway first | Proposed |
| 21 | Suggestions are a scheduled workflow (not an agent); rules pick products, a template writes text | Cheap, safe, testable | Proposed |
| 22 | Aggregator model (OnePay); no direct merchant account | Fast sign-up for a small business | Proposed |
| 23 | Later: a reconciliation job in payment-service | Catch missing or double payments | Idea |
| 24 | Confirm OnePay has a server-side callback or verify-transaction API before building | The browser return alone is not safe | Open |
| 27 | Suggestion message from a fixed template; template text lives in config, not Java | Keeps services reusable | Proposed |
| 28 | Recommendations: a separate Python recommendation-service using a maintained LightFM fork; content-based + collaborative | Handles few orders (cold start) and purchases | Proposed |
| 30 | Train the model on a timer and save it; serving reads the saved model | Training is slow; serving must be fast | Proposed |
| 31 | Build SQL-rule suggestions first as a fallback; add LightFM after the system runs | A weak library never blocks emails | Proposed |
| 32 | Develop on WSL, but run recommendation-service inside Docker | Same image on laptop and in production | Proposed |
| 33 | recommendation-service: Python 3.12, FastAPI, lightfm-next, port 8085 | Chosen stack for the Python service | Proposed |
