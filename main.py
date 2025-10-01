from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Dict, Any
import time
import uuid
import uvicorn

from app.routers import patient_router, health_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import ConectaSaudeException

# Global logger
logger = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    global logger
    setup_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)
    
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    
    yield
    
    logger.info("Encerrando aplicação")

# Criar aplicação FastAPI com Swagger otimizado
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "root",
            "description": "🏠 Endpoint principal da API"
        },
        {
            "name": "health",
            "description": "🏥 Endpoints de saúde e monitoramento do sistema"
        },
        {
            "name": "patient",
            "description": "👤 Análise e processamento de dados de pacientes com IA"
        }
    ],
    contact={
        "name": "Equipe Conecta+Saúde",
        "email": "conectasaude@recife.pe.gov.br",
        "url": "https://github.com/conectasaude/api"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": f"http://localhost:8082",
            "description": "Servidor de Desenvolvimento"
        },
        {
            "url": f"https://api.conectasaude.recife.pe.gov.br",
            "description": "Servidor de Produção"
        }
    ]
)

# Middleware de logging
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware para logging de requisições"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    request.state.request_id = request_id
    
    if logger:
        logger.info(
            "Requisição recebida",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None
            }
        )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    if logger:
        logger.info(
            "Requisição processada",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": int(process_time * 1000)
            }
        )
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    
    return response

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# Exception handlers
@app.exception_handler(ConectaSaudeException)
async def conecta_saude_exception_handler(request: Request, exc: ConectaSaudeException):
    """Handler para exceções de negócio"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    if logger:
        logger.error(
            "Exceção de negócio",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação do Pydantic"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    if logger:
        logger.warning(
            "Erro de validação de entrada",
            extra={
                "request_id": request_id,
                "validation_errors": exc.errors()
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Dados de entrada inválidos",
            "details": exc.errors(),
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções não tratadas"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    if logger:
        logger.error(
            "Erro interno não tratado",
            extra={
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            },
            exc_info=True
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),  # Sempre mostrar erro detalhado (modo desenvolvimento)
            "request_id": request_id
        }
    )

# Incluir routers
app.include_router(health_router.router)
app.include_router(patient_router.router)

# Endpoint Hello World
@app.get(
    "/hello",
    summary="Hello World",
    description="Endpoint simples que retorna uma mensagem de boas-vindas",
    tags=["root"],
    responses={
        200: {
            "description": "Mensagem de sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Hello World! 🌍",
                        "timestamp": "2025-10-01T12:00:00Z",
                        "service": "Conecta+Saúde API"
                    }
                }
            }
        }
    }
)
async def hello_world() -> Dict[str, Any]:
    """
    Endpoint simples Hello World
    
    Retorna uma mensagem de boas-vindas com informações básicas do serviço.
    Útil para testar a conectividade básica da API.
    """
    from datetime import datetime
    
    return {
        "message": "Hello World! 🌍",
        "timestamp": datetime.now().isoformat() + "Z",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "success ✅"
    }

# Endpoint raiz
@app.get(
    "/",
    summary="Informações da API",
    description="Endpoint raiz com informações gerais da API",
    tags=["root"]
)
async def root() -> Dict[str, Any]:
    """Endpoint raiz com informações da API"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online ✅",
        "description": settings.APP_DESCRIPTION,
        "endpoints": {
            "hello": "/hello - Hello World simples",
            "health": "/health - Health checks",
            "patients": f"{settings.API_V1_PREFIX}/patient - Análise de pacientes",
            "docs": f"{settings.DOCS_URL} - Documentação interativa" if settings.DOCS_URL else "Desabilitado em produção"
        },
        "features": {
            "classification": "Classificação ML de outliers",
            "recommendations": "Geração de recomendações com IA",
            "monitoring": "Health checks e métricas",
            "logging": "Logging estruturado"
        }
    }

if __name__ == "__main__":
    if logger:
        logger.info(
            "Iniciando servidor de desenvolvimento",
            extra={
                "host": settings.HOST,
                "port": settings.PORT,
                "reload": settings.DEBUG
            }
        )
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True  # Sempre mostrar logs de acesso (modo desenvolvimento)
    )