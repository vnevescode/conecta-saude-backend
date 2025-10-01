# Makefile simplificado para MVP

.PHONY: help install run test docker-build docker-run clean

# Variáveis
PYTHON := python
PIP := pip

help: ## Mostrar ajuda
	@echo "Conecta+Saúde API - Comandos MVP"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Instalar dependências
	$(PIP) install -r requirements.txt

run: ## Executar aplicação
	$(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8082 --reload

test: ## Executar testes básicos
	$(PYTHON) -c "import requests; print('Health check:', requests.get('http://localhost:8082/health').status_code)"

docker-build: ## Build da imagem Docker
	docker build -t conecta-saude-api .

docker-run: ## Executar com Docker
	docker-compose up -d

clean: ## Limpar cache Python
	find . -type d -name "__pycache__" -delete
	find . -name "*.pyc" -delete