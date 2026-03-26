# Agate demo — local Docker only

COMPOSE_FILE = infra/docker-compose.yml
WOF_DIR = packages/utils/src/agate_utils/geocoding/data
WOF_DB = $(WOF_DIR)/whosonfirst-data-admin-us-latest.db
WOF_BZ2 = $(WOF_DB).bz2
WOF_URL = https://data.geocode.earth/wof/dist/sqlite/whosonfirst-data-admin-us-latest.db.bz2

.PHONY: up down download-wof

download-wof: ## Download and extract Who's On First DB if missing (geocoding)
	@if [ -f "$(WOF_DB)" ]; then \
		echo "Who's On First database already present ($(WOF_DB)), skipping download."; \
	else \
		echo "Creating $(WOF_DIR)..."; \
		mkdir -p "$(WOF_DIR)"; \
		echo "Downloading Who's On First database..."; \
		curl -fL -o "$(WOF_BZ2)" "$(WOF_URL)"; \
		echo "Extracting database..."; \
		bunzip2 "$(WOF_BZ2)"; \
		echo "✅ Who's On First database ready at $(WOF_DB)"; \
	fi

up: download-wof
	@echo "Starting stack (postgres, redis, agate-api, worker, agate-ui)..."
	@docker compose -f $(COMPOSE_FILE) up

down:
	@echo "🛑 Stopping services..."
	@docker compose -f $(COMPOSE_FILE) down
	@echo "🧹 Pruning unused Docker resources..."
	@docker system prune -f
	@docker volume prune -f
	@echo "✅ Done."
