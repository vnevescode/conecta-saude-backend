from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class RiskLevel(str, Enum):
    """Níveis de risco do paciente"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatientDataInput(BaseModel):
    """DTO para entrada de dados do paciente"""
    idade: int = Field(
        ..., 
        ge=0, 
        le=120, 
        description="Idade do paciente em anos"
    )
    nivel_glicose: float = Field(
        ..., 
        ge=0, 
        le=1000, 
        description="Nível de glicose em mg/dL"
    )
    pressao_sistolica: int = Field(
        ..., 
        ge=60, 
        le=300, 
        description="Pressão sistólica em mmHg"
    )
    pressao_diastolica: int = Field(
        ..., 
        ge=40, 
        le=200, 
        description="Pressão diastólica em mmHg"
    )
    historico_familiar: bool = Field(
        ..., 
        description="Se possui histórico familiar de diabetes/hipertensão"
    )
    
    @field_validator('nivel_glicose')
    @classmethod
    def validate_glucose_level(cls, v):
        if v < 0:
            raise ValueError('Nível de glicose não pode ser negativo')
        if v > 800:  # Valor extremamente alto, provavelmente erro
            raise ValueError('Nível de glicose muito alto, verificar dados')
        return v
    
    @model_validator(mode='after')
    def validate_blood_pressure(self):
        if self.pressao_sistolica <= self.pressao_diastolica:
            raise ValueError(
                'Pressão sistólica deve ser maior que a diastólica'
            )
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "idade": 65,
                "nivel_glicose": 140.5,
                "pressao_sistolica": 130,
                "pressao_diastolica": 85,
                "historico_familiar": True
            }
        }
    }


class PatientData(PatientDataInput):
    """Entidade de domínio do paciente (para uso interno)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def blood_pressure_formatted(self) -> str:
        return f"{self.pressao_sistolica}/{self.pressao_diastolica}"
    
    @property
    def risk_indicators(self) -> Dict[str, bool]:
        """Indicadores de risco baseados nos dados"""
        return {
            "high_glucose": self.nivel_glicose > 200,
            "hypertension": self.pressao_sistolica > 140 or self.pressao_diastolica > 90,
            "severe_hypertension": self.pressao_sistolica > 160 or self.pressao_diastolica > 100,
            "elderly": self.idade > 65,
            "family_history": self.historico_familiar
        }


class ClassificationResult(BaseModel):
    """Resultado da classificação ML"""
    is_outlier: bool = Field(..., description="Se o paciente é um outlier")
    confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Confiança da classificação (0-1)"
    )
    risk_level: Optional[RiskLevel] = Field(
        None, 
        description="Nível de risco calculado"
    )
    classification_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da classificação"
    )


class RecommendationData(BaseModel):
    """Dados da recomendação gerada"""
    content: str = Field(..., description="Conteúdo da recomendação")
    priority: str = Field(default="normal", description="Prioridade da ação")
    generated_by: str = Field(default="system", description="Sistema que gerou")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da geração"
    )


class PatientAnalysisResponse(BaseModel):
    """DTO de resposta da análise do paciente"""
    analysis_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="ID único da análise"
    )
    patient_data: PatientDataInput = Field(..., description="Dados do paciente")
    classification: ClassificationResult = Field(
        ..., 
        description="Resultado da classificação"
    )
    recommendation: Optional[RecommendationData] = Field(
        None, 
        description="Recomendação gerada se necessário"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da análise"
    )
    processing_time_ms: Optional[int] = Field(
        None, 
        description="Tempo de processamento em milissegundos"
    )
    
    # Properties for backward compatibility
    @property
    def is_outlier(self) -> bool:
        return self.classification.is_outlier
    
    @property
    def confidence(self) -> Optional[float]:
        return self.classification.confidence
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "patient_data": {
                    "idade": 65,
                    "nivel_glicose": 280,
                    "pressao_sistolica": 160,
                    "pressao_diastolica": 95,
                    "historico_familiar": True
                },
                "classification": {
                    "is_outlier": True,
                    "confidence": 0.89,
                    "risk_level": "high",
                    "classification_timestamp": "2025-09-30T10:30:00Z"
                },
                "recommendation": {
                    "content": "1. URGENTE: Contatar paciente imediatamente...\n2. Agendar consulta de emergência...",
                    "priority": "urgent",
                    "generated_by": "llm_service",
                    "generated_at": "2025-09-30T10:30:00Z"
                },
                "analysis_timestamp": "2025-09-30T10:30:00Z",
                "processing_time_ms": 1250
            }
        }
    }