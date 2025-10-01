"""
Sistema de logging simplificado para MVP
"""
import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configura o sistema de logging simples"""
    
    # Configurar nível de log
    log_level_enum = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar logging básico
    logging.basicConfig(
        level=log_level_enum,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """Obtém um logger configurado"""
    return logging.getLogger(name)