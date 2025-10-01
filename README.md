# 🏥 Conecta+Saúde API - MVP

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.108+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

API Backend minimalista para análise de pacientes com IA, desenvolvida com **FastAPI** seguindo princípios **Clean Code**, **DRY**, **KISS** e **YAGNI**.

> 🎯 **MVP Otimizado**: Código limpo, essencial e direto ao ponto.

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
cd conecta-saude-fastapi
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas chaves
# GEMINI_API_KEY=sua_chave_do_google_gemini
# CLASSIFICATION_SERVICE_URL=http://localhost:8082
```

### 3. Executar o Servidor
```bash
# Opção 1: Usando uvicorn diretamente
uvicorn main:app --reload --host 0.0.0.0 --port 8082

# Opção 2: Usando o script main.py
python main.py
```

### 4. Testar
- **Documentação**: http://localhost:8082/docs
- **Health Check**: http://localhost:8082/health
- **Endpoint de Teste**: http://localhost:8082/patient/test

## 🧪 Testando o Endpoint Principal

### Teste Simples (GET)
```bash
curl http://localhost:8082/patient/test
```

### Análise de Paciente (POST)
```bash
curl -X POST "http://localhost:8082/patient/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "idade": 65,
       "nivel_glicose": 280,
       "pressao_sistolica": 160,
       "pressao_diastolica": 95,
       "historico_familiar": true
     }'
```

## 📁 Estrutura do Projeto

```
conecta-saude-fastapi/
├── main.py                     # Ponto de entrada
├── requirements.txt            # Dependências
├── .env.example               # Exemplo de configuração
└── app/
    ├── core/
    │   └── config.py          # Configurações
    ├── models/
    │   └── patient.py         # Modelos Pydantic
    ├── services/
    │   ├── classification_service.py  # Classificação ML
    │   ├── llm_service.py            # Google Gemini
    │   └── patient_service.py        # Lógica principal
    └── routers/
        ├── health_router.py   # Health checks
        └── patient_router.py  # Endpoints de paciente
```

## 🔄 Equivalências NestJS → FastAPI

| NestJS | FastAPI | Descrição |
|--------|---------|----------|
| `@Controller('patient')` | `router = APIRouter(prefix="/patient")` | Definição de rotas |
| `@Post('analyze')` | `@router.post("/analyze")` | Endpoint POST |
| `@Injectable()` | `def get_service()` | Injeção de dependência |
| `PatientService` | `PatientService` | Lógica de negócio |
| `ClassificationService` | `ClassificationService` | Serviço ML |
| `LlmService` | `LLMService` | Serviço LLM |

## 🛠️ Funcionalidades

- ✅ **Análise de Pacientes**: Detecta outliers
- ✅ **Integração LLM**: Google Gemini para recomendações
- ✅ **Classificação ML**: Mock interno + integração externa
- ✅ **Validação**: Pydantic para validação de dados
- ✅ **Documentação**: Swagger UI automática
- ✅ **Health Checks**: Monitoramento de saúde da API
- ✅ **CORS**: Configurado para frontend

## 🔧 Desenvolvimento

```bash
# Modo desenvolvimento com auto-reload
uvicorn main:app --reload

# Instalar dependências de desenvolvimento
pip install pytest httpx

# Executar testes (quando implementados)
pytest
```