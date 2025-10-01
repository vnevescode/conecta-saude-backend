import httpx
from typing import Dict, Any
from datetime import datetime
from app.models.patient import ClassificationResult, RiskLevel
from app.core.config import settings
from app.core.interfaces import IClassificationService
from app.core.exceptions import ClassificationServiceException, ExternalServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClassificationStrategy:
    """Estratégia para classificação de risco (Pattern Strategy)"""
    
    @staticmethod
    def calculate_risk_level(patient_data: Dict[str, Any]) -> RiskLevel:
        """Calcula nível de risco baseado em critérios médicos"""
        idade = patient_data.get("idade", 0)
        glicose = patient_data.get("nivel_glicose", 0)
        sistolica = patient_data.get("pressao_sistolica", 0)
        diastolica = patient_data.get("pressao_diastolica", 0)
        historico = patient_data.get("historico_familiar", False)
        
        # Critérios críticos
        if (
            glicose > 300 or
            sistolica > 180 or
            diastolica > 110
        ):
            return RiskLevel.CRITICAL
        
        # Critérios de alto risco
        critical_conditions = sum([
            glicose > 200,  # Diabetes severa
            sistolica > 160,  # Hipertensão severa
            diastolica > 100,  # Hipertensão diastólica severa
            idade > 70 and glicose > 140,  # Idoso diabético
            idade > 80,  # Idade muito avançada
        ])
        
        if critical_conditions >= 2:
            return RiskLevel.HIGH
        elif critical_conditions == 1 or (historico and (glicose > 126 or sistolica > 140)):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    @staticmethod
    def is_outlier(risk_level: RiskLevel) -> bool:
        """Determina se é outlier baseado no nível de risco"""
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @staticmethod
    def calculate_confidence(risk_level: RiskLevel, patient_data: Dict[str, Any]) -> float:
        """Calcula confiança da classificação"""
        base_confidence = {
            RiskLevel.CRITICAL: 0.95,
            RiskLevel.HIGH: 0.85,
            RiskLevel.MEDIUM: 0.75,
            RiskLevel.LOW: 0.70
        }
        
        confidence = base_confidence[risk_level]
        
        # Ajustar confiança baseada em completude dos dados
        required_fields = ["idade", "nivel_glicose", "pressao_sistolica", "pressao_diastolica"]
        completeness = sum(1 for field in required_fields if patient_data.get(field) is not None) / len(required_fields)
        
        return min(confidence * completeness, 0.99)


class ClassificationService(IClassificationService):
    """Serviço para classificação de outliers usando ML externo ou lógica local"""
    
    def __init__(self):
        self.classification_url = settings.CLASSIFICATION_SERVICE_URL
        self.timeout = 30.0
        self.strategy = ClassificationStrategy()
    
    async def classify(self, patient_data: Dict[str, Any]) -> ClassificationResult:
        """Classifica paciente usando serviço ML externo ou fallback local"""
        
        logger.info(
            "Iniciando classificação",
            extra={
                "patient_age": patient_data.get("idade"),
                "glucose_level": patient_data.get("nivel_glicose"),
                "has_external_service": bool(self.classification_url)
            }
        )
        
        if not self.classification_url:
            logger.info("Usando classificação local (sem serviço externo configurado)")
            return await self._local_classification(patient_data)
        
        try:
            return await self._external_classification(patient_data)
        except (ClassificationServiceException, ExternalServiceException) as e:
            logger.warning(f"Falha no serviço externo, usando fallback local: {e}")
            return await self._local_classification(patient_data)
        except Exception as e:
            logger.error(f"Erro inesperado na classificação: {e}")
            raise ClassificationServiceException(
                "Falha crítica na classificação",
                details={"original_error": str(e)}
            )
    
    async def _external_classification(self, patient_data: Dict[str, Any]) -> ClassificationResult:
        """Classificação usando serviço ML externo"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.classification_url}/classify",
                    json=patient_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info("Classificação externa concluída com sucesso")
                
                return ClassificationResult(
                    is_outlier=data.get("is_outlier", False),
                    confidence=data.get("confidence", 0.5),
                    risk_level=data.get("risk_level", RiskLevel.MEDIUM),
                    classification_timestamp=datetime.now()
                )
                
        except httpx.TimeoutException:
            raise ExternalServiceException(
                "classification", "Timeout na requisição"
            )
        except httpx.RequestError as e:
            raise ExternalServiceException(
                "classification", f"Erro de conexão: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise ExternalServiceException(
                "classification", 
                f"Erro HTTP {e.response.status_code}: {e.response.text}"
            )
    
    async def _local_classification(self, patient_data: Dict[str, Any]) -> ClassificationResult:
        """Classificação local usando regras de negócio"""
        
        risk_level = self.strategy.calculate_risk_level(patient_data)
        is_outlier = self.strategy.is_outlier(risk_level)
        confidence = self.strategy.calculate_confidence(risk_level, patient_data)
        
        logger.info(
            "Classificação local concluída",
            extra={
                "risk_level": risk_level,
                "is_outlier": is_outlier,
                "confidence": confidence
            }
        )
        
        return ClassificationResult(
            is_outlier=is_outlier,
            confidence=confidence,
            risk_level=risk_level,
            classification_timestamp=datetime.now()
        )