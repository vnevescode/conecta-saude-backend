from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time
import uuid

from app.models.patient import PatientDataInput, PatientAnalysisResponse
from app.services.patient_service import PatientService
from app.core.exceptions import (
    ConectaSaudeException, 
    ValidationException, 
    ClassificationServiceException,
    LLMServiceException
)
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/patient",
    tags=["patient"],
    responses={
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro interno do servidor"},
        503: {"description": "Serviço indisponível"}
    }
)

# Dependency Injection
def get_patient_service() -> PatientService:
    """Factory para o serviço de pacientes"""
    return PatientService()

# Middleware para logging de requests
async def log_request_middleware(request: Request, call_next):
    """Middleware para logging de requisições"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Adicionar request_id ao contexto
    request.state.request_id = request_id
    
    logger.info(f"Processing request {request_id}: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Request processado",
        extra={
            "request_id": request_id,
            "process_time_ms": int(process_time * 1000),
            "status_code": response.status_code
        }
    )
    
    # Adicionar headers de response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    
    return response

@router.post(
    "/analyze", 
    response_model=PatientAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analisar Paciente",
    description="Analisa dados de um paciente e gera recomendações se necessário"
)
async def analyze_patient(
    patient_data: PatientDataInput,
    request: Request,
    patient_service: PatientService = Depends(get_patient_service)
) -> PatientAnalysisResponse:
    """
    **Endpoint Principal - Análise de Paciente**
    
    Realiza análise completa de um paciente seguindo o fluxo:
    
    1. **Validação**: Verifica dados de entrada
    2. **Classificação**: Determina se é outlier usando ML
    3. **Recomendação**: Gera ações se necessário
    4. **Resposta**: Retorna análise completa
    
    **Casos de Uso:**
    - Triagem automática de pacientes
    - Identificação de casos prioritários
    - Geração de planos de ação
    """
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        logger.info(
            "Iniciando análise de paciente",
            extra={
                "request_id": request_id,
                "patient_age": patient_data.idade,
                "glucose_level": patient_data.nivel_glicose,
                "blood_pressure": f"{patient_data.pressao_sistolica}/{patient_data.pressao_diastolica}",
                "family_history": patient_data.historico_familiar
            }
        )
        
        # Chama o Application Service
        result = await patient_service.analyze_patient(patient_data)
        
        logger.info(
            "Análise concluída com sucesso",
            extra={
                "request_id": request_id,
                "analysis_id": result.analysis_id,
                "is_outlier": result.is_outlier,
                "risk_level": result.classification.risk_level,
                "processing_time_ms": result.processing_time_ms
            }
        )
        
        return result
        
    except ValidationException as e:
        logger.warning(
            "Erro de validação",
            extra={
                "request_id": request_id,
                "error": e.message,
                "field": getattr(e, 'field', None)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VALIDATION_ERROR",
                "message": e.message,
                "field": getattr(e, 'field', None),
                "request_id": request_id
            }
        )
    
    except ClassificationServiceException as e:
        logger.error(
            "Erro no serviço de classificação",
            extra={"request_id": request_id, "error": e.message}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "CLASSIFICATION_SERVICE_ERROR",
                "message": "Serviço de classificação temporiamente indisponível",
                "request_id": request_id
            }
        )
    
    except LLMServiceException as e:
        logger.error(
            "Erro no serviço de LLM",
            extra={"request_id": request_id, "error": e.message}
        )
        # LLM não é crítico, continuamos com fallback
        raise HTTPException(
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            detail={
                "error": "LLM_SERVICE_ERROR",
                "message": "Análise concluída com recomendação básica",
                "request_id": request_id
            }
        )
    
    except ConectaSaudeException as e:
        logger.error(
            "Erro de negócio",
            extra={
                "request_id": request_id,
                "error_code": e.error_code,
                "error": e.message
            }
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "request_id": request_id
            }
        )
    
    except Exception as e:
        logger.error(
            "Erro interno inesperado",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Erro interno do servidor",
                "request_id": request_id
            }
        )

@router.get(
    "/health",
    summary="Health Check do Serviço de Pacientes",
    description="Verifica saúde dos serviços dependentes"
)
async def patient_service_health(
    patient_service: PatientService = Depends(get_patient_service)
) -> Dict[str, Any]:
    """Health check específico do serviço de pacientes"""
    try:
        health_status = await patient_service.get_health_status()
        return {
            "status": "healthy",
            "service": "patient_service",
            **health_status
        }
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "patient_service",
                "error": str(e)
            }
        )

@router.get(
    "/test",
    summary="Endpoint de Teste",
    description="Endpoint simples para verificar funcionamento básico"
)
async def test_endpoint() -> Dict[str, Any]:
    """
    **Endpoint de Teste**
    
    Retorna informações básicas sobre o serviço e exemplos de uso.
    """
    return {
        "message": "🏥 Serviço de Pacientes - Online",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "analyze": f"POST {settings.API_V1_PREFIX}/patient/analyze - Analisa paciente",
            "health": f"GET {settings.API_V1_PREFIX}/patient/health - Health check",
            "test": f"GET {settings.API_V1_PREFIX}/patient/test - Este endpoint"
        },
        "example_request": {
            "method": "POST",
            "url": f"{settings.API_V1_PREFIX}/patient/analyze",
            "body": {
                "idade": 65,
                "nivel_glicose": 280.5,
                "pressao_sistolica": 160,
                "pressao_diastolica": 95,
                "historico_familiar": True
            }
        },
        "expected_response": {
            "analysis_id": "uuid",
            "patient_data": "...",
            "classification": {
                "is_outlier": True,
                "confidence": 0.89,
                "risk_level": "high"
            },
            "recommendation": {
                "content": "Ações recomendadas...",
                "priority": "urgent"
            }
        }
    }