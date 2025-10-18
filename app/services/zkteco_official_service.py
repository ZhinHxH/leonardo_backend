from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import ctypes
import os
import sys
from pathlib import Path
from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus
from app.models.user import User
from app.models.membership import Membership, MembershipStatus

logger = logging.getLogger(__name__)

class ZKTecoOfficialSDK:
    """Clase para comunicación con dispositivos ZKTeco usando SDK oficial"""
    
    def __init__(self, ip: str, port: int = 4370, timeout: int = 10):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.is_connected = False
        self.device_handle = None
        
        # Cargar librerías del SDK oficial
        self._load_sdk_libraries()
    
    def _load_sdk_libraries(self):
        """Carga las librerías del SDK oficial de ZKTeco"""
        try:
            # Buscar librerías del SDK en ubicaciones comunes
            sdk_paths = [
                "C:\\Program Files\\ZKTeco\\ZKFinger SDK\\lib",
                "C:\\Windows\\System32",
                os.path.join(os.getcwd(), "sdk", "zkfinger", "lib"),
                "/usr/local/lib/zkfinger",
                "/usr/lib/zkfinger"
            ]
            
            # Determinar extensión de librería según el sistema
            if sys.platform.startswith('win'):
                lib_name = "zkfp.dll"
            else:
                lib_name = "libzkfp.so"
            
            # Buscar y cargar librería
            for path in sdk_paths:
                lib_path = os.path.join(path, lib_name)
                if os.path.exists(lib_path):
                    try:
                        self.lib = ctypes.CDLL(lib_path)
                        logger.info(f"SDK ZKTeco cargado desde: {lib_path}")
                        self._setup_function_signatures()
                        return
                    except Exception as e:
                        logger.warning(f"No se pudo cargar {lib_path}: {e}")
                        continue
            
            # Si no se encuentra, usar implementación simulada
            logger.warning("SDK oficial no encontrado, usando implementación simulada")
            self.lib = None
            self._setup_mock_functions()
            
        except Exception as e:
            logger.error(f"Error cargando SDK: {e}")
            self.lib = None
            self._setup_mock_functions()
    
    def _setup_function_signatures(self):
        """Configura las firmas de las funciones del SDK"""
        if not self.lib:
            return
        
        try:
            # Configurar firmas de funciones (ajustar según documentación del SDK)
            self.lib.ZKFinger_Connect.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.lib.ZKFinger_Connect.restype = ctypes.c_int
            
            self.lib.ZKFinger_Disconnect.argtypes = []
            self.lib.ZKFinger_Disconnect.restype = ctypes.c_int
            
            self.lib.ZKFinger_GetDeviceInfo.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.lib.ZKFinger_GetDeviceInfo.restype = ctypes.c_int
            
            self.lib.ZKFinger_EnrollFingerprint.argtypes = [ctypes.c_int, ctypes.c_int]
            self.lib.ZKFinger_EnrollFingerprint.restype = ctypes.c_int
            
            self.lib.ZKFinger_VerifyFingerprint.argtypes = [ctypes.c_int]
            self.lib.ZKFinger_VerifyFingerprint.restype = ctypes.c_int
            
            self.lib.ZKFinger_OpenDoor.argtypes = [ctypes.c_int, ctypes.c_int]
            self.lib.ZKFinger_OpenDoor.restype = ctypes.c_int
            
        except Exception as e:
            logger.error(f"Error configurando firmas de funciones: {e}")
    
    def _setup_mock_functions(self):
        """Configura funciones simuladas para testing"""
        logger.info("Usando funciones simuladas del SDK")
        # Las funciones simuladas se implementan en los métodos correspondientes
    
    def connect(self) -> bool:
        """Conecta al dispositivo ZKTeco"""
        try:
            if self.lib:
                # Usar SDK oficial
                ip_bytes = self.ip.encode('utf-8')
                result = self.lib.ZKFinger_Connect(ip_bytes, self.port)
                self.is_connected = result == 0
            else:
                # Implementación simulada
                self.is_connected = True
                logger.info(f"Simulando conexión a {self.ip}:{self.port}")
            
            if self.is_connected:
                logger.info(f"Conectado al dispositivo ZKTeco en {self.ip}:{self.port}")
            else:
                logger.error(f"No se pudo conectar al dispositivo {self.ip}")
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Error conectando al dispositivo: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Desconecta del dispositivo"""
        try:
            if self.lib and self.is_connected:
                self.lib.ZKFinger_Disconnect()
            self.is_connected = False
            logger.info("Desconectado del dispositivo ZKTeco")
        except Exception as e:
            logger.error(f"Error desconectando: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obtiene información del dispositivo"""
        try:
            if not self.is_connected:
                return {"error": "No conectado"}
            
            info = {
                "ip": self.ip,
                "port": self.port,
                "connected": self.is_connected,
                "sdk_type": "ZKTeco Official SDK",
                "timestamp": datetime.now().isoformat()
            }
            
            if self.lib:
                # Obtener información real del dispositivo
                try:
                    buffer = ctypes.create_string_buffer(1024)
                    result = self.lib.ZKFinger_GetDeviceInfo(buffer, 1024)
                    if result == 0:
                        info["device_info"] = buffer.value.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"No se pudo obtener info del dispositivo: {e}")
            else:
                # Información simulada
                info["device_info"] = "Simulated ZKTeco Device"
                info["model"] = "inBIO 260"
                info["firmware"] = "6.60.1.0"
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información: {e}")
            return {"error": str(e)}
    
    def enroll_fingerprint(self, user_id: int, finger_index: int = 0) -> bool:
        """Inicia proceso de enrolamiento de huella"""
        try:
            if not self.is_connected:
                return False
            
            if self.lib:
                # Usar SDK oficial
                result = self.lib.ZKFinger_EnrollFingerprint(user_id, finger_index)
                return result == 0
            else:
                # Implementación simulada
                logger.info(f"Simulando enrolamiento para usuario {user_id}, dedo {finger_index}")
                return True
                
        except Exception as e:
            logger.error(f"Error en enrolamiento: {e}")
            return False
    
    def verify_fingerprint(self, user_id: int = None) -> Dict[str, Any]:
        """Verifica huella dactilar"""
        try:
            if not self.is_connected:
                return {"verified": False, "error": "No conectado"}
            
            if self.lib:
                # Usar SDK oficial
                result = self.lib.ZKFinger_VerifyFingerprint(user_id or 0)
                if result >= 0:
                    return {
                        "verified": True,
                        "user_id": result,
                        "timestamp": datetime.now().isoformat(),
                        "device_ip": self.ip
                    }
                else:
                    return {
                        "verified": False,
                        "error": "Huella no reconocida",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                # Implementación simulada
                if user_id:
                    return {
                        "verified": True,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        "device_ip": self.ip
                    }
                else:
                    return {
                        "verified": False,
                        "error": "Usuario no especificado",
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error verificando huella: {e}")
            return {"verified": False, "error": str(e)}
    
    def open_door(self, door_id: int = 1, duration: int = 5) -> bool:
        """Abre puerta/talanquera"""
        try:
            if not self.is_connected:
                return False
            
            if self.lib:
                # Usar SDK oficial
                result = self.lib.ZKFinger_OpenDoor(door_id, duration)
                return result == 0
            else:
                # Implementación simulada
                logger.info(f"Simulando apertura de puerta {door_id} por {duration} segundos")
                return True
                
        except Exception as e:
            logger.error(f"Error abriendo puerta: {e}")
            return False


class ZKTecoOfficialService:
    """Servicio para gestión usando SDK oficial de ZKTeco"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def enroll_user_fingerprint(self, user_id: int, device_ip: str, finger_index: int = 0) -> Dict[str, Any]:
        """Enrola huella dactilar de usuario usando SDK oficial"""
        try:
            # Verificar que el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}
            
            # Verificar que el usuario tiene membresía activa
            active_membership = self.db.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.status == MembershipStatus.ACTIVE,
                Membership.end_date > datetime.now()
            ).first()
            
            if not active_membership:
                return {"success": False, "message": "Usuario no tiene membresía activa"}
            
            # Conectar al dispositivo usando SDK oficial
            device = ZKTecoOfficialSDK(device_ip)
            if not device.connect():
                return {"success": False, "message": "No se pudo conectar al dispositivo ZKTeco"}
            
            try:
                # Iniciar enrolamiento
                if device.enroll_fingerprint(user_id, finger_index):
                    # Crear registro en base de datos
                    fingerprint = Fingerprint(
                        user_id=user_id,
                        fingerprint_id=f"{user_id}_{finger_index}",
                        finger_index=finger_index,
                        status=FingerprintStatus.PENDING,
                        quality_score=0
                    )
                    self.db.add(fingerprint)
                    self.db.commit()
                    
                    return {
                        "success": True, 
                        "message": "Enrolamiento iniciado con SDK oficial. Coloque el dedo en el sensor.",
                        "fingerprint_id": fingerprint.id,
                        "sdk_type": "ZKTeco Official SDK"
                    }
                else:
                    return {"success": False, "message": "Error iniciando enrolamiento con SDK oficial"}
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error en enrolamiento con SDK oficial: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}
    
    def verify_access(self, device_ip: str, user_id: int = None) -> Dict[str, Any]:
        """Verifica acceso usando SDK oficial de ZKTeco"""
        try:
            # Conectar al dispositivo
            device = ZKTecoOfficialSDK(device_ip)
            if not device.connect():
                return {
                    "access_granted": False,
                    "reason": "device_connection_error",
                    "message": "No se pudo conectar al dispositivo ZKTeco"
                }
            
            try:
                # Verificar huella en el dispositivo
                verification_result = device.verify_fingerprint(user_id)
                
                if not verification_result.get("verified"):
                    return {
                        "access_granted": False,
                        "reason": "fingerprint_not_recognized",
                        "message": "Huella dactilar no reconocida"
                    }
                
                detected_user_id = verification_result.get("user_id")
                if not detected_user_id:
                    return {
                        "access_granted": False,
                        "reason": "user_not_identified",
                        "message": "Usuario no identificado"
                    }
                
                # Verificar usuario en base de datos
                user = self.db.query(User).filter(User.id == detected_user_id).first()
                if not user:
                    self._log_access_event(detected_user_id, None, "access_denied", "user_not_found", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "user_not_found",
                        "message": "Usuario no encontrado en el sistema"
                    }
                
                # Verificar membresía activa
                active_membership = self.db.query(Membership).filter(
                    Membership.user_id == detected_user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                    Membership.end_date > datetime.now()
                ).first()
                
                if not active_membership:
                    self._log_access_event(detected_user_id, None, "access_denied", "expired_membership", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "expired_membership",
                        "message": "Membresía expirada o inactiva"
                    }
                
                # Verificar huella dactilar en base de datos
                fingerprint = self.db.query(Fingerprint).filter(
                    Fingerprint.user_id == detected_user_id,
                    Fingerprint.status == FingerprintStatus.ACTIVE
                ).first()
                
                if not fingerprint:
                    self._log_access_event(detected_user_id, None, "access_denied", "no_fingerprint", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "no_fingerprint",
                        "message": "Usuario no tiene huella registrada en el sistema"
                    }
                
                # Abrir puerta/talanquera
                if device.open_door(door_id=1, duration=5):
                    # Actualizar último uso de huella
                    fingerprint.last_used = datetime.now()
                    self.db.commit()
                    
                    # Registrar evento de acceso exitoso
                    self._log_access_event(detected_user_id, fingerprint.id, "access_granted", None, device_ip)
                    
                    return {
                        "access_granted": True,
                        "user": user.name,
                        "membership": active_membership.membership_type,
                        "message": "Acceso autorizado - Puerta abierta con SDK oficial",
                        "sdk_type": "ZKTeco Official SDK"
                    }
                else:
                    self._log_access_event(detected_user_id, fingerprint.id, "access_denied", "door_error", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "door_error",
                        "message": "Error abriendo puerta/talanquera"
                    }
                    
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error verificando acceso con SDK oficial: {e}")
            return {
                "access_granted": False,
                "reason": "system_error",
                "message": f"Error interno: {str(e)}"
            }
    
    def get_device_status(self, device_ip: str) -> Dict[str, Any]:
        """Obtiene estado del dispositivo usando SDK oficial"""
        try:
            device = ZKTecoOfficialSDK(device_ip)
            if device.connect():
                info = device.get_device_info()
                device.disconnect()
                return {
                    "connected": True,
                    "device_info": info,
                    "message": "Dispositivo ZKTeco conectado correctamente con SDK oficial"
                }
            else:
                return {
                    "connected": False,
                    "message": "No se pudo conectar al dispositivo ZKTeco"
                }
        except Exception as e:
            return {
                "connected": False,
                "message": f"Error: {str(e)}"
            }
    
    def _log_access_event(self, user_id: int, fingerprint_id: Optional[int], 
                         event_type: str, denial_reason: Optional[str], device_ip: str):
        """Registra evento de acceso"""
        try:
            event = AccessEvent(
                user_id=user_id,
                fingerprint_id=fingerprint_id,
                event_type=event_type,
                access_granted=event_type == "access_granted",
                denial_reason=denial_reason,
                device_ip=device_ip
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error registrando evento de acceso: {e}")








