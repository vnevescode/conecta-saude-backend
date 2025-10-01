"""
Interfaces e contratos para os serviços (preparando para DDD)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.patient import ClassificationResult, RecommendationData


class IClassificationService(ABC):
    """Interface para serviço de classificação"""
    
    @abstractmethod
    async def classify(self, patient_data: Dict[str, Any]) -> ClassificationResult:
        """Classifica um paciente como outlier ou não"""
        pass


class ILLMService(ABC):
    """Interface para serviço de LLM"""
    
    @abstractmethod
    async def generate_recommendation(
        self, 
        patient_data: Dict[str, Any],
        classification_result: ClassificationResult
    ) -> RecommendationData:
        """Gera recomendação personalizada"""
        pass


class IPatientRepository(ABC):
    """Interface para repositório de pacientes (futuro)"""
    
    @abstractmethod
    async def save_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Salva análise do paciente"""
        pass
    
    @abstractmethod
    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Recupera análise por ID"""
        pass


class IHealthService(ABC):
    """Interface para verificações de health check"""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Verifica saúde do serviço"""
        pass