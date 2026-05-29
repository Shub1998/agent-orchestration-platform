.PHONY: setup dev demo stop clean help

help:
	@echo "AgentFlow - AI Agent Orchestration Platform"
	@echo ""
	@echo "Commands:"
	@echo "  make setup    - First-time setup: copy .env and build containers"
	@echo "  make dev      - Start all services (backend + worker + frontend)"
	@echo "  make telegram - Start with Telegram bot enabled"
	@echo "  make demo     - Seed demo data and start"
	@echo "  make stop     - Stop all containers"
	@echo "  make clean    - Remove all containers and volumes"
	@echo "  make logs     - Tail all service logs"

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env — please add your API keys!"; fi
	@docker compose build
	@echo "\n✅ Setup complete! Run 'make dev' to start."

dev:
	@docker compose up

telegram:
	@docker compose --profile telegram up

demo:
	@if [ ! -f .env ]; then cp .env.example .env && echo "⚠️  Add your OPENAI_API_KEY to .env first!"; fi
	@docker compose up -d redis backend worker beat
	@sleep 5
	@echo "Seeding demo templates..."
	@curl -s -X POST http://localhost:8000/api/v1/templates/research-pipeline/instantiate | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Research Pipeline:', d.get('workflow_id', 'created'))"
	@curl -s -X POST http://localhost:8000/api/v1/templates/customer-support/instantiate | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Customer Support:', d.get('workflow_id', 'created'))"
	@docker compose up frontend
	@echo "\n🚀 AgentFlow is running!"
	@echo "   UI:  http://localhost:3001"
	@echo "   API: http://localhost:8000/docs"

stop:
	@docker compose down

clean:
	@docker compose down -v --remove-orphans
	@rm -rf backend/data

logs:
	@docker compose logs -f
