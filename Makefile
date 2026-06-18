.PHONY: logs
logs:
	docker compose logs -f

.PHONY: down
down:
	docker compose down

.PHONY: up
up:
	docker compose up -d --build

.PHONY: up-follow
up-follow:
	docker compose up -d --build
	@$(MAKE) logs

.PHONY: reload
reload:
	@$(MAKE) down
	@$(MAKE) up

.PHONY: reload-follow
reload-follow:
	@$(MAKE) down
	@$(MAKE) up-follow

.PHONY: help
help:
	@grep '^[a-zA-Z_-]*:' Makefile | cut -d':' -f1