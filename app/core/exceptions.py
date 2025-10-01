"""
Exceções customizadas para o domínio da aplicação
"""
from typing import Optional, Any, Dict


class ConectaSaudeException(Exception):
    """Exceção base para todas as exceções da aplicação"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ConectaSaudeException):
    """Exceção para erros de validação de dados"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class ClassificationServiceException(ConectaSaudeException):
    """Exceção para erros no serviço de classificação"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CLASSIFICATION_ERROR", **kwargs)


class LLMServiceException(ConectaSaudeException):
    """Exceção para erros no serviço de LLM"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="LLM_ERROR", **kwargs)


class ExternalServiceException(ConectaSaudeException):
    """Exceção para erros em serviços externos"""
    
    def __init__(self, service_name: str, message: str, **kwargs):
        super().__init__(
            f"Erro no serviço {service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            **kwargs
        )
        self.service_name = service_name


class ConfigurationException(ConectaSaudeException):
    """Exceção para erros de configuração"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)