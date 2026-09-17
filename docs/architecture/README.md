# motoXpress architecture docs

This folder holds the architecture of motoXpress, a vehicle part ordering
system built with Spring Boot microservices. It follows the C4 model:
zoom in from the whole system to one service.

| File | What it shows |
|---|---|
| [01-context-diagram.md](01-context-diagram.md) | Context diagram (level 1): the system, its users, and outside systems |
| [02-container-diagram.md](02-container-diagram.md) | Container diagram (level 2): the gateway, services, databases, and how they talk |
| [06-event-contracts.md](06-event-contracts.md) | RabbitMQ event contract: exchange, event names, queues, message body |
| [decisions.md](decisions.md) | The list of architecture decisions and why |

More diagrams (component) will be added later.
