from typing import Dict, Any, Optional
from datetime import datetime
from app.models.patient import RecommendationData, ClassificationResult, RiskLevel
from app.core.config import settings
from app.core.interfaces import ILLMService
from app.core.exceptions import LLMServiceException
from app.core.logging import get_logger

# Temporariamente desabilitando Google AI para testes
GEMINI_AVAILABLE = False
genai = None

logger = get_logger(__name__)


class RecommendationBuilder:
    """Builder para construção de recomendações (Pattern Builder)"""
    
    def __init__(self):
        self.recommendations = []
        self.priority = "normal"
    
    def add_urgent_contact(self, hours: int = 24) -> 'RecommendationBuilder':
        self.recommendations.append(
            f"1. 🚨 URGENTE: Contatar paciente em até {hours}h para agendamento prioritário"
        )
        self.priority = "urgent"
        return self
    
    def add_medical_appointment(self, urgency: str = "urgência") -> 'RecommendationBuilder':
        self.recommendations.append(f"2. 📅 Agendar consulta médica de {urgency}")
        return self
    
    def add_glucose_monitoring(self, level: float) -> 'RecommendationBuilder':
        if level > 300:
            self.recommendations.extend([
                "3. 🩸 URGENTE: Glicemia capilar de 2/2h até estabilização",
                "4. 🩸 Solicitar IMEDIATO: Hemoglobina glicada (HbA1c)",
                "5. 👨‍⚕️ Encaminhamento IMEDIATO para endocrinologista"
            ])
        elif level > 200:
            self.recommendations.extend([
                "3. 🩸 Solicitar: Hemoglobina glicada, glicemia de jejum e pós-prandial",
                "4. 👨‍⚕️ Encaminhar para endocrinologista em 7 dias"
            ])
        return self
    
    def add_pressure_monitoring(self, systolic: int, diastolic: int) -> 'RecommendationBuilder':
        if systolic > 180 or diastolic > 110:
            self.recommendations.extend([
                "3. 📊 Monitoramento pressão arterial de 2/2h",
                "4. 💊 Reavaliação URGENTE da medicação anti-hipertensiva",
                "5. ⚠️ Orientar sobre sinais de crise hipertensiva"
            ])
        elif systolic > 160 or diastolic > 100:
            self.recommendations.extend([
                "3. 📊 Monitoramento diário da pressão arterial",
                "4. 💊 Revisar medicação anti-hipertensiva"
            ])
        return self
    
    def add_elderly_care(self, age: int) -> 'RecommendationBuilder':
        if age > 80:
            self.recommendations.append("6. 👴 Acompanhamento geriátrico URGENTE")
        elif age > 65:
            self.recommendations.append("6. 👴 Acompanhamento geriátrico especializado")
        return self
    
    def add_family_guidance(self, has_family_history: bool) -> 'RecommendationBuilder':
        if has_family_history:
            self.recommendations.append(
                "7. 👨‍👩‍👧‍👦 Orientar família sobre fatores de risco hereditários"
            )
        return self
    
    def add_lifestyle_guidance(self, risk_level: RiskLevel) -> 'RecommendationBuilder':
        if risk_level == RiskLevel.CRITICAL:
            self.recommendations.append("8. 🥗 Orientação nutricional URGENTE")
        else:
            self.recommendations.append("8. 🥗 Orientar sobre hábitos alimentares e exercícios")
        return self
    
    def add_followup(self, days: int) -> 'RecommendationBuilder':
        self.recommendations.append(f"9. 📞 Retorno obrigatório em {days} dias")
        return self
    
    def build(self) -> str:
        return "\n".join(self.recommendations)
    
    def get_priority(self) -> str:
        return self.priority


class PromptTemplate:
    """Template para construção de prompts (Pattern Template Method)"""
    
    @staticmethod
    def build_medical_prompt(
        patient_data: Dict[str, Any], 
        classification: ClassificationResult
    ) -> str:
        """Constrói prompt médico contextualizado"""
        
        risk_context = {
            RiskLevel.CRITICAL: "CASO CRÍTICO - REQUER AÇÃO IMEDIATA",
            RiskLevel.HIGH: "CASO DE ALTO RISCO - PRIORIDADE ALTA",
            RiskLevel.MEDIUM: "CASO DE RISCO MÉDIO - ACOMPANHAMENTO NECESSÁRIO",
            RiskLevel.LOW: "CASO DE BAIXO RISCO - ACOMPANHAMENTO ROTINA"
        }
        
        return f"""
Você é um especialista em saúde pública da Secretaria de Saúde do Recife.

**CLASSIFICAÇÃO: {risk_context.get(classification.risk_level, 'NÃO CLASSIFICADO')}**
**CONFIANÇA: {classification.confidence:.1%}**

**DADOS DO PACIENTE:**
- Idade: {patient_data.get('idade')} anos
- Glicose: {patient_data.get('nivel_glicose')} mg/dL
- Pressão Arterial: {patient_data.get('pressao_sistolica')}/{patient_data.get('pressao_diastolica')} mmHg
- Histórico Familiar: {'Sim' if patient_data.get('historico_familiar') else 'Não'}

**TAREFA:**
Gere um plano de ação objetivo em tópicos numerados para a equipe de saúde.

**DIRETRIZES:**
• Seja direto e prático
• Priorize ações por urgência
• Inclua prazos específicos
• Foque em ações executáveis
• Use emojis para facilitar identificação rápida

**FORMATO:** Lista numerada com ações específicas.
"""


class LLMService(ILLMService):
    """Serviço para geração de recomendações usando LLM ou fallback local"""
    
    def __init__(self):
        self.model = None
        self.builder = RecommendationBuilder()
        
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("LLM configurado com sucesso (Gemini)")
            except Exception as e:
                logger.warning(f"Falha ao configurar Gemini: {e}")
        else:
            logger.info("LLM não configurado, usando recomendações locais")
    
    async def generate_recommendation(
        self, 
        patient_data: Dict[str, Any],
        classification_result: ClassificationResult
    ) -> RecommendationData:
        """Gera recomendação personalizada"""
        
        logger.info(
            "Gerando recomendação",
            extra={
                "risk_level": classification_result.risk_level,
                "is_outlier": classification_result.is_outlier,
                "has_llm": bool(self.model)
            }
        )
        
        try:
            if self.model and classification_result.is_outlier:
                content = await self._generate_llm_recommendation(
                    patient_data, classification_result
                )
                priority = self._determine_priority(classification_result.risk_level)
                generated_by = "gemini_llm"
            else:
                content = self._generate_local_recommendation(
                    patient_data, classification_result
                )
                priority = self._determine_priority(classification_result.risk_level)
                generated_by = "local_rules"
            
            logger.info(f"Recomendação gerada por: {generated_by}")
            
            return RecommendationData(
                content=content,
                priority=priority,
                generated_by=generated_by,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Erro na geração de recomendação: {e}")
            # Fallback para recomendação básica
            return RecommendationData(
                content=self._generate_basic_recommendation(),
                priority="normal",
                generated_by="fallback",
                generated_at=datetime.now()
            )
    
    async def _generate_llm_recommendation(
        self, 
        patient_data: Dict[str, Any],
        classification: ClassificationResult
    ) -> str:
        """Gera recomendação usando LLM"""
        try:
            prompt = PromptTemplate.build_medical_prompt(patient_data, classification)
            
            # Timeout para evitar travamento
            import asyncio
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt),
                timeout=30.0
            )
            
            return response.text.strip()
            
        except asyncio.TimeoutError:
            raise LLMServiceException("Timeout na geração da recomendação")
        except Exception as e:
            raise LLMServiceException(f"Erro no LLM: {str(e)}")
    
    def _generate_local_recommendation(
        self, 
        patient_data: Dict[str, Any],
        classification: ClassificationResult
    ) -> str:
        """Gera recomendação usando regras locais (Pattern Builder)"""
        
        idade = patient_data.get('idade', 0)
        glicose = patient_data.get('nivel_glicose', 0)
        sistolica = patient_data.get('pressao_sistolica', 0)
        diastolica = patient_data.get('pressao_diastolica', 0)
        historico = patient_data.get('historico_familiar', False)
        
        builder = RecommendationBuilder()
        
        if classification.risk_level == RiskLevel.CRITICAL:
            builder.add_urgent_contact(2)  # 2 horas
        elif classification.risk_level == RiskLevel.HIGH:
            builder.add_urgent_contact(12)  # 12 horas
        else:
            builder.add_urgent_contact(24)  # 24 horas
        
        builder.add_medical_appointment("urgência" if classification.is_outlier else "rotina")
        
        if glicose > 140:
            builder.add_glucose_monitoring(glicose)
        
        if sistolica > 140 or diastolica > 90:
            builder.add_pressure_monitoring(sistolica, diastolica)
        
        if idade > 65:
            builder.add_elderly_care(idade)
        
        builder.add_family_guidance(historico)
        builder.add_lifestyle_guidance(classification.risk_level)
        
        followup_days = {
            RiskLevel.CRITICAL: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.MEDIUM: 15,
            RiskLevel.LOW: 30
        }
        builder.add_followup(followup_days.get(classification.risk_level, 15))
        
        return builder.build()
    
    def _generate_basic_recommendation(self) -> str:
        """Recomendação básica para casos de erro"""
        return (
            "1. Contatar paciente para agendamento\n"
            "2. Agendar consulta médica\n"
            "3. Orientar sobre acompanhamento regular"
        )
    
    def _determine_priority(self, risk_level: Optional[RiskLevel]) -> str:
        """Determina prioridade baseada no nível de risco"""
        priority_map = {
            RiskLevel.CRITICAL: "critical",
            RiskLevel.HIGH: "urgent",
            RiskLevel.MEDIUM: "high",
            RiskLevel.LOW: "normal"
        }
        return priority_map.get(risk_level, "normal")