from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any
import psutil
import sys

from app.core.config import settings
from app.core.logging import get_logger
from app.services.classification_service import ClassificationService
from app.services.llm_service import LLMService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        200: {"description": "Serviço saudável"},
        503: {"description": "Serviço indisponível"}
    }
)

def get_system_metrics() -> Dict[str, Any]:
    """Obtém métricas do sistema"""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if sys.platform != 'win32' else psutil.disk_usage('C:\\').percent,
            "python_version": sys.version.split()[0],
            "process_id": psutil.Process().pid
        }
    except Exception as e:
        logger.warning(f"Erro ao obter métricas do sistema: {e}")
        return {"error": "metrics_unavailable"}

async def check_external_services() -> Dict[str, str]:
    """Verifica saúde dos serviços externos"""
    services_status = {}
    
    # Verificar serviço de classificação
    try:
        classification_service = ClassificationService()
        if classification_service.classification_url:
            # TODO: Implementar ping real ao serviço
            services_status["classification_service"] = "configured"
        else:
            services_status["classification_service"] = "using_local_fallback"
    except Exception:
        services_status["classification_service"] = "error"
    
    # Verificar serviço de LLM
    try:
        llm_service = LLMService()
        if llm_service.model:
            services_status["llm_service"] = "configured"
        else:
            services_status["llm_service"] = "using_local_fallback"
    except Exception:
        services_status["llm_service"] = "error"
    
    return services_status

@router.get(
    "/",
    summary="Health Check Básico",
    description="Verificação básica de saúde da API"
)
async def health_check() -> Dict[str, Any]:
    """Endpoint de health check básico"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "uptime_check": "ok"
    }

@router.get(
    "/ready",
    summary="Readiness Check",
    description="Verifica se o serviço está pronto para receber requisições"
)
async def readiness_check() -> JSONResponse:
    """Endpoint de readiness check com verificação de dependências"""
    
    try:
        services_status = await check_external_services()
        
        # Determinar status geral
        all_healthy = all(
            status in ["configured", "using_local_fallback"] 
            for status in services_status.values()
        )
        
        response_data = {
            "status": "ready" if all_healthy else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "online",
                **services_status
            },
            "checks": {
                "database": "not_implemented",  # Para futuro
                "external_apis": "checked",
                "configuration": "loaded"
            }
        }
        
        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_200_OK
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Erro no readiness check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": settings.APP_NAME,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@router.get(
    "/live",
    summary="Liveness Check",
    description="Verifica se o serviço está vivo (para Kubernetes)"
)
async def liveness_check() -> Dict[str, Any]:
    """Endpoint de liveness check (para Kubernetes)"""
    return {
        "status": "alive",
        "service": settings.APP_NAME,
        "timestamp": datetime.now().isoformat(),
        "process_id": psutil.Process().pid
    }

@router.get(
    "/metrics",
    summary="Métricas do Sistema",
    description="Retorna métricas detalhadas do sistema (para monitoring)"
)
async def metrics_endpoint() -> Dict[str, Any]:
    """Endpoint de métricas para monitoring"""
    
    try:
        system_metrics = get_system_metrics()
        services_status = await check_external_services()
        
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "services": services_status,
            "configuration": {
                "debug_mode": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "api_prefix": settings.API_V1_PREFIX
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "metrics_unavailable",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )