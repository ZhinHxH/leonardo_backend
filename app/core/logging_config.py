import asyncio
import logging
import logging.handlers
import sys
import traceback
import re
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import json
from fastapi import HTTPException

def remove_emojis(text):
    """Elimina emojis del texto para compatibilidad con Windows console"""
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", re.UNICODE)
    return emoji_pattern.sub(r'', text)

class ConsoleFormatter(logging.Formatter):
    """Formatter para consola sin emojis"""
    
    def format(self, record):
        # Eliminar emojis del mensaje para evitar problemas de codificación
        original_msg = record.getMessage()
        clean_msg = remove_emojis(original_msg)
        
        # Crear un nuevo record con el mensaje limpio
        record.msg = clean_msg
        record.args = ()
        
        return super().format(record)

class StructuredFormatter(logging.Formatter):
    """Formatter personalizado para logs estructurados"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Agregar información adicional si existe
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
            
        return json.dumps(log_entry, ensure_ascii=False, indent=2)

class ErrorTracker:
    """Clase para rastrear y categorizar errores"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_contexts = {}
    
    def track_error(self, error_type: str, context: Dict[str, Any] = None):
        """Rastrea un error con su contexto"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        if context:
            if error_type not in self.error_contexts:
                self.error_contexts[error_type] = []
            self.error_contexts[error_type].append({
                'timestamp': datetime.utcnow().isoformat(),
                'context': context
            })
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de errores"""
        return {
            'error_counts': self.error_counts,
            'error_contexts': self.error_contexts
        }

# Instancia global del tracker de errores
error_tracker = ErrorTracker()

def setup_logging():
    """Configura el sistema de logging"""
    
    # Crear logger principal
    logger = logging.getLogger('gym_system')
    logger.setLevel(logging.INFO)
    
    # Evitar duplicación de logs
    if logger.handlers:
        return logger
    
    # Handler para consola (sin emojis para evitar problemas de codificación en Windows)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ConsoleFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Handler para archivo con rotación (con encoding UTF-8)
    file_handler = logging.handlers.RotatingFileHandler(
        'app.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    
    # Handler para errores críticos (con encoding UTF-8)
    error_handler = logging.handlers.RotatingFileHandler(
        'errors.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    
    # Agregar handlers al logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

def log_exception(logger: logging.Logger, exception: Exception, context: Dict[str, Any] = None):
    """Función helper para loggear excepciones con contexto"""
    error_type = type(exception).__name__
    
    # Rastrear el error
    error_tracker.track_error(error_type, context)
    
    # Loggear con contexto
    extra_data = {
        'exception_type': error_type,
        'exception_message': str(exception),
        'context': context or {}
    }
    
    logger.error(
        f"💥 Excepción capturada: {error_type} - {str(exception)}",
        exc_info=True,
        extra={'extra_data': extra_data}
    )

def exception_handler(logger: logging.Logger, context: Dict[str, Any] = None):
    """Decorador para capturar excepciones automáticamente (funciones síncronas y asíncronas)"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    logger.info(f"🔄 Ejecutando {func.__name__} con args: {len(args)}, kwargs: {len(kwargs)}")
                    result = await func(*args, **kwargs)
                    logger.info(f"✅ {func.__name__} ejecutado exitosamente")
                    return result
                except HTTPException:
                    # Re-lanzar HTTPException sin logging adicional
                    raise
                except Exception as e:
                    # Crear contexto de error
                    error_context = {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()),
                        **(context or {})
                    }
                    
                    log_exception(logger, e, error_context)
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    logger.info(f"🔄 Ejecutando {func.__name__} con args: {len(args)}, kwargs: {len(kwargs)}")
                    result = func(*args, **kwargs)
                    logger.info(f"✅ {func.__name__} ejecutado exitosamente")
                    return result
                except HTTPException:
                    # Re-lanzar HTTPException sin logging adicional
                    raise
                except Exception as e:
                    # Crear contexto de error
                    error_context = {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()),
                        **(context or {})
                    }
                    
                    log_exception(logger, e, error_context)
                    raise
            return sync_wrapper
    return decorator

def log_function_call(logger: logging.Logger):
    """Decorador para loggear llamadas a funciones (síncronas y asíncronas)"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger.info(f"📞 Llamada a {func.__name__} desde {func.__module__}")
                start_time = datetime.utcnow()
                
                try:
                    result = await func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(f"⏱️ {func.__name__} completado en {duration:.3f}s")
                    return result
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.error(f"❌ {func.__name__} falló después de {duration:.3f}s: {str(e)}")
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                logger.info(f"📞 Llamada a {func.__name__} desde {func.__module__}")
                start_time = datetime.utcnow()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(f"⏱️ {func.__name__} completado en {duration:.3f}s")
                    return result
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.error(f"❌ {func.__name__} falló después de {duration:.3f}s: {str(e)}")
                    raise
            return sync_wrapper
    return decorator

# Configurar logging al importar el módulo
main_logger = setup_logging()
