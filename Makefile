# Agate demo — local Docker only

COMPOSE_FILE = infra/docker-compose.yml

.PHONY: up down

up:
	@echo "Starting stack (postgres, redis, agate-api, worker, agate-ui)..."
	@docker compose -f $(COMPOSE_FILE) up

down:
	@echo "🛑 Stopping services..."
	@docker compose -f $(COMPOSE_FILE) down
	@echo "🧹 Pruning unused Docker resources..."
	@docker system prune -f
	@docker volume prune -f
	@echo "✅ Done."
