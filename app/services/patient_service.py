from typing import Dict, Any, Optional
from datetime import datetime
import time
from app.models.patient import (
    PatientDataInput, 
    PatientData, 
    PatientAnalysisResponse,
    ClassificationResult,
    RecommendationData
)
from app.services.classification_service import ClassificationService
from app.services.llm_service import LLMService
from app.core.exceptions import ValidationException, ConectaSaudeException
from app.core.logging import get_logger

logger = get_logger(__name__)


class PatientAnalysisMetrics:
    """Métricas de análise (preparando para observabilidade)"""
    
    def __init__(self):
        self.start_time = time.time()
        self.classification_time: Optional[float] = None
        self.recommendation_time: Optional[float] = None
        self.total_time: Optional[float] = None
    
    def mark_classification_complete(self):
        self.classification_time = time.time() - self.start_time
    
    def mark_recommendation_complete(self):
        if self.classification_time:
            self.recommendation_time = time.time() - self.start_time - self.classification_time
    
    def mark_complete(self):
        self.total_time = time.time() - self.start_time
    
    def get_total_time_ms(self) -> int:
        return int((self.total_time or 0) * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification_time_ms": int((self.classification_time or 0) * 1000),
            "recommendation_time_ms": int((self.recommendation_time or 0) * 1000),
            "total_time_ms": self.get_total_time_ms()
        }


class PatientService:
    """Serviço principal para análise de pacientes (Application Service - DDD)"""
    
    def __init__(
        self,
        classification_service: Optional[ClassificationService] = None,
        llm_service: Optional[LLMService] = None
    ):
        # Dependency Injection (preparando para DI container)
        self.classification_service = classification_service or ClassificationService()
        self.llm_service = llm_service or LLMService()
    
    async def analyze_patient(self, patient_input: PatientDataInput) -> PatientAnalysisResponse:
        """Analisa paciente completo - Caso de uso principal"""
        
        metrics = PatientAnalysisMetrics()
        
        # Converter para entidade de domínio
        patient_data = PatientData(**patient_input.dict())
        
        logger.info(
            "Iniciando análise do paciente",
            extra={
                "patient_id": patient_data.id,
                "patient_age": patient_data.idade,
                "glucose_level": patient_data.nivel_glicose,
                "blood_pressure": patient_data.blood_pressure_formatted
            }
        )
        
        try:
            # 1. Classificação
            classification_result = await self._classify_patient(patient_data)
            metrics.mark_classification_complete()
            
            # 2. Geração de recomendação (se necessário)
            recommendation_data = await self._generate_recommendation(
                patient_data, classification_result
            )
            metrics.mark_recommendation_complete()
            
            # 3. Persistência (futuro)
            # await self._save_analysis(patient_data, classification_result, recommendation_data)
            
            metrics.mark_complete()
            
            # 4. Construção da resposta
            response = PatientAnalysisResponse(
                patient_data=patient_input,
                classification=classification_result,
                recommendation=recommendation_data,
                processing_time_ms=metrics.get_total_time_ms()
            )
            
            logger.info(
                "Análise concluída com sucesso",
                extra={
                    "patient_id": patient_data.id,
                    "is_outlier": classification_result.is_outlier,
                    "risk_level": classification_result.risk_level,
                    "has_recommendation": recommendation_data is not None,
                    **metrics.to_dict()
                }
            )
            
            return response
            
        except ConectaSaudeException:
            # Re-raise business exceptions
            raise
        except Exception as e:
            logger.error(
                "Erro inesperado na análise do paciente",
                extra={
                    "patient_id": patient_data.id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise ConectaSaudeException(
                "Falha crítica na análise do paciente",
                details={"original_error": str(e)}
            )
    
    async def _classify_patient(self, patient_data: PatientData) -> ClassificationResult:
        """Classifica o paciente usando o serviço de classificação"""
        try:
            patient_dict = patient_data.dict(exclude={"id", "created_at"})
            classification_result = await self.classification_service.classify(patient_dict)
            
            logger.info(
                "Classificação concluída",
                extra={
                    "patient_id": patient_data.id,
                    "is_outlier": classification_result.is_outlier,
                    "confidence": classification_result.confidence,
                    "risk_level": classification_result.risk_level
                }
            )
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            raise
    
    async def _generate_recommendation(
        self, 
        patient_data: PatientData, 
        classification_result: ClassificationResult
    ) -> Optional[RecommendationData]:
        """Gera recomendação se necessário"""
        
        # Só gera recomendação para outliers ou casos de risco
        if not classification_result.is_outlier:
            logger.info(
                "Paciente dentro dos parâmetros normais, sem recomendação especial",
                extra={"patient_id": patient_data.id}
            )
            return None
        
        try:
            logger.info(
                "Gerando recomendação para paciente outlier",
                extra={
                    "patient_id": patient_data.id,
                    "risk_level": classification_result.risk_level
                }
            )
            
            patient_dict = patient_data.dict(exclude={"id", "created_at"})
            recommendation_data = await self.llm_service.generate_recommendation(
                patient_dict, classification_result
            )
            
            logger.info(
                "Recomendação gerada com sucesso",
                extra={
                    "patient_id": patient_data.id,
                    "recommendation_length": len(recommendation_data.content),
                    "priority": recommendation_data.priority,
                    "generated_by": recommendation_data.generated_by
                }
            )
            
            return recommendation_data
            
        except Exception as e:
            logger.error(
                "Erro na geração de recomendação",
                extra={
                    "patient_id": patient_data.id,
                    "error": str(e)
                }
            )
            # Em caso de erro, retorna recomendação básica
            return RecommendationData(
                content="Agendar consulta médica para avaliação detalhada",
                priority="normal",
                generated_by="fallback"
            )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Verifica saúde dos serviços dependentes"""
        return {
            "patient_service": "healthy",
            "classification_service": "healthy",
            "llm_service": "healthy",
            "timestamp": datetime.now().isoformat()
        }