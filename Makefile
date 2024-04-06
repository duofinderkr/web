.PHONY: server
server:
	@echo "Starting server..."
	@poetry run python project/manage.py runserver 22145


.PHONY: infra
infra:
	@echo "Starting infra..."
	@docker-compose -f docker-compose-dev.yaml up -d --force-recreate --build