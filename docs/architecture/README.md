# motoXpress architecture docs

This folder holds the architecture of motoXpress, a vehicle part ordering
system built with Spring Boot microservices.

It follows the **C4 model**. C4 is a way to draw software like a map:
you start zoomed out, then zoom in one step at a time.

| C4 level | Question it answers | Our file |
|---|---|---|
| 1. Context | Who uses the system, and which outside systems does it call? | [01-context-diagram.md](01-context-diagram.md) |
| 2. Container | Which parts run on their own, and how do they talk? | [02-container-diagram.md](02-container-diagram.md) |
| 3. Component | What is inside one service? | [03-components/](03-components/) (coming) |
| Dynamic | In what order do things happen in one scenario? | [04-dynamic/](04-dynamic/) (coming) |
| Deployment | Where does each part run (laptop, cloud)? | [05-deployment/](05-deployment/) (coming) |
| 4. Code | Classes and methods | Not drawn. The code itself shows this. |

Supporting files (not C4, but you need them to build the services):

| File | What it shows |
|---|---|
| [06-event-contracts.md](06-event-contracts.md) | Every RabbitMQ event: name, sender, queues, message body |
| [07-data-model.md](07-data-model.md) | The tables of each database (coming) |
| [08-state-diagrams.md](08-state-diagrams.md) | The life of an order and a payment (coming) |
| [09-api-map.md](09-api-map.md) | Every URL, which service owns it, and the ports |
| [decisions.md](decisions.md) | Every architecture decision and why |

## Reading order

1. Context → 2. Container → 9. API map → 6. Event contract.
2. Then, for the service you are about to build: its component diagram, its tables
   in the data model, and the dynamic flows it takes part in.

## How to read every diagram

The same shapes mean the same thing in every file.

| Shape | Meaning |
|---|---|
| `([ rounded ])` | A person (customer, admin) |
| `[ box ]` | Our own service, or a part inside a service |
| `[( cylinder )]` | A database or data store |
| `{{ hexagon }}` | RabbitMQ (the message broker) |
| `[/ slanted /]` | A RabbitMQ queue |
| `[[ double box ]]` | An outside system (someone else runs it) |
| Solid arrow `-->` | HTTP. The caller waits for the answer. |
| Dotted arrow `-.->` | An event. The sender does not wait. |

Status words on boxes:

- **Built** = the code exists today.
- **Planned** = a design for code we have not written yet. It may still change.

Anything marked **Open** or **TODO** is not decided. Do not build it until it is decided.

## Small glossary

| Word | Meaning |
|---|---|
| Event | A message that says "this happened", for example `order.paid` |
| Exchange | The RabbitMQ part that receives every event and copies it to the right queues |
| Queue | A waiting line of messages for one listening service |
| Binding | A rule: "copy events with this name into this queue" |
| Webhook | An outside system calls **our** URL to tell us something |
| Domain-free | The service has no shop words in its code, so another project can reuse it |
| Idempotent | Doing it twice gives the same result as doing it once |
