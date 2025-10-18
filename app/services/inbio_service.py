from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import time
from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus
from app.models.user import User
from app.models.membership import Membership, MembershipStatus
from app.core.database import get_db

logger = logging.getLogger(__name__)

try:
    from pyzkaccess import ZKAccess, ZKAccessError
    PYZKACCESS_AVAILABLE = True
except ImportError:
    PYZKACCESS_AVAILABLE = False
    logger.warning("pyzkaccess no está disponible. Instala con: pip install pyzkaccess")


class InBIODevice:
    """Clase para comunicación con paneles inBIO de ZKTeco"""
    
    def __init__(self, ip: str, port: int = 4370, timeout: int = 10):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.zk = None
        self.is_connected = False
        
        if not PYZKACCESS_AVAILABLE:
            raise ImportError("pyzkaccess no está instalado. Ejecuta: pip install pyzkaccess")
    
    def connect(self) -> bool:
        """Conecta al panel inBIO"""
        try:
            self.zk = ZKAccess(self.ip, self.port, timeout=self.timeout)
            self.zk.connect()
            self.is_connected = True
            logger.info(f"Conectado al panel inBIO en {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Error conectando al panel inBIO {self.ip}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Desconecta del panel inBIO"""
        if self.zk and self.is_connected:
            try:
                self.zk.disconnect()
            except:
                pass
            self.zk = None
            self.is_connected = False
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obtiene información del dispositivo"""
        try:
            if not self.is_connected:
                return {"error": "No conectado"}
            
            # Obtener información básica del dispositivo
            info = {
                "ip": self.ip,
                "port": self.port,
                "connected": self.is_connected,
                "device_type": "inBIO",
                "timestamp": datetime.now().isoformat()
            }
            
            # Intentar obtener información adicional del dispositivo
            try:
                # Esto puede variar según el modelo específico de inBIO
                device_info = self.zk.get_device_info()
                info.update(device_info)
            except:
                # Si no se puede obtener info adicional, usar la básica
                pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del dispositivo: {e}")
            return {"error": str(e)}
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Obtiene lista de usuarios del panel"""
        try:
            if not self.is_connected:
                return []
            
            users = []
            # Obtener usuarios del panel inBIO
            # La implementación exacta depende del modelo específico
            try:
                # Ejemplo de cómo obtener usuarios (ajustar según documentación)
                user_list = self.zk.get_users()
                for user in user_list:
                    users.append({
                        "user_id": user.get("user_id"),
                        "name": user.get("name"),
                        "card_number": user.get("card_number"),
                        "privilege": user.get("privilege"),
                        "password": user.get("password")
                    })
            except Exception as e:
                logger.warning(f"No se pudieron obtener usuarios: {e}")
            
            return users
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def enroll_fingerprint(self, user_id: int, finger_index: int = 0) -> bool:
        """Inicia proceso de enrolamiento de huella"""
        try:
            if not self.is_connected:
                return False
            
            # Iniciar enrolamiento en el panel inBIO
            # La implementación exacta depende del modelo específico
            try:
                # Ejemplo de enrolamiento (ajustar según documentación)
                result = self.zk.enroll_fingerprint(user_id, finger_index)
                return result
            except Exception as e:
                logger.error(f"Error en enrolamiento: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error iniciando enrolamiento: {e}")
            return False
    
    def verify_fingerprint(self, user_id: int = None) -> Dict[str, Any]:
        """Verifica huella dactilar y retorna información del usuario"""
        try:
            if not self.is_connected:
                return {"verified": False, "error": "No conectado"}
            
            # Verificar huella en el panel inBIO
            # El panel debería retornar el user_id si la verificación es exitosa
            try:
                # Ejemplo de verificación (ajustar según documentación)
                verification_result = self.zk.verify_fingerprint()
                
                if verification_result.get("verified"):
                    return {
                        "verified": True,
                        "user_id": verification_result.get("user_id"),
                        "timestamp": datetime.now().isoformat(),
                        "device_ip": self.ip
                    }
                else:
                    return {
                        "verified": False,
                        "error": "Huella no reconocida",
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Error en verificación: {e}")
                return {"verified": False, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Error verificando huella: {e}")
            return {"verified": False, "error": str(e)}
    
    def open_door(self, door_id: int = 1, duration: int = 5) -> bool:
        """Abre puerta/talanquera"""
        try:
            if not self.is_connected:
                return False
            
            # Abrir puerta en el panel inBIO
            try:
                # Ejemplo de apertura de puerta (ajustar según documentación)
                result = self.zk.open_door(door_id, duration)
                return result
            except Exception as e:
                logger.error(f"Error abriendo puerta: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error abriendo puerta: {e}")
            return False
    
    def get_attendance_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene logs de asistencia del panel"""
        try:
            if not self.is_connected:
                return []
            
            logs = []
            try:
                # Obtener logs de asistencia
                attendance_logs = self.zk.get_attendance_logs(limit=limit)
                for log in attendance_logs:
                    logs.append({
                        "user_id": log.get("user_id"),
                        "timestamp": log.get("timestamp"),
                        "event_type": log.get("event_type"),
                        "door_id": log.get("door_id"),
                        "verify_mode": log.get("verify_mode")
                    })
            except Exception as e:
                logger.warning(f"No se pudieron obtener logs: {e}")
            
            return logs
            
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []


class InBIOService:
    """Servicio para gestión de paneles inBIO"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def enroll_user_fingerprint(self, user_id: int, device_ip: str, finger_index: int = 0) -> Dict[str, Any]:
        """Enrola huella dactilar de usuario en panel inBIO"""
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
            
            # Conectar al panel inBIO
            device = InBIODevice(device_ip)
            if not device.connect():
                return {"success": False, "message": "No se pudo conectar al panel inBIO"}
            
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
                        "message": "Enrolamiento iniciado en panel inBIO. Coloque el dedo en el sensor.",
                        "fingerprint_id": fingerprint.id
                    }
                else:
                    return {"success": False, "message": "Error iniciando enrolamiento en panel inBIO"}
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error en enrolamiento inBIO: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}
    
    def verify_access(self, device_ip: str) -> Dict[str, Any]:
        """Verifica acceso basado en huella dactilar y membresía"""
        try:
            # Conectar al panel inBIO
            device = InBIODevice(device_ip)
            if not device.connect():
                return {
                    "access_granted": False,
                    "reason": "device_connection_error",
                    "message": "No se pudo conectar al panel inBIO"
                }
            
            try:
                # Verificar huella en el panel
                verification_result = device.verify_fingerprint()
                
                if not verification_result.get("verified"):
                    return {
                        "access_granted": False,
                        "reason": "fingerprint_not_recognized",
                        "message": "Huella dactilar no reconocida"
                    }
                
                user_id = verification_result.get("user_id")
                if not user_id:
                    return {
                        "access_granted": False,
                        "reason": "user_not_identified",
                        "message": "Usuario no identificado"
                    }
                
                # Verificar usuario en base de datos
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    self._log_access_event(user_id, None, "access_denied", "user_not_found", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "user_not_found",
                        "message": "Usuario no encontrado en el sistema"
                    }
                
                # Verificar membresía activa
                active_membership = self.db.query(Membership).filter(
                    Membership.user_id == user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                    Membership.end_date > datetime.now()
                ).first()
                
                if not active_membership:
                    self._log_access_event(user_id, None, "access_denied", "expired_membership", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "expired_membership",
                        "message": "Membresía expirada o inactiva"
                    }
                
                # Verificar huella dactilar en base de datos
                fingerprint = self.db.query(Fingerprint).filter(
                    Fingerprint.user_id == user_id,
                    Fingerprint.status == FingerprintStatus.ACTIVE
                ).first()
                
                if not fingerprint:
                    self._log_access_event(user_id, None, "access_denied", "no_fingerprint", device_ip)
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
                    self._log_access_event(user_id, fingerprint.id, "access_granted", None, device_ip)
                    
                    return {
                        "access_granted": True,
                        "user": user.name,
                        "membership": active_membership.membership_type,
                        "message": "Acceso autorizado - Puerta abierta"
                    }
                else:
                    self._log_access_event(user_id, fingerprint.id, "access_denied", "door_error", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "door_error",
                        "message": "Error abriendo puerta/talanquera"
                    }
                    
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error verificando acceso inBIO: {e}")
            return {
                "access_granted": False,
                "reason": "system_error",
                "message": f"Error interno: {str(e)}"
            }
    
    def sync_attendance_logs(self, device_ip: str, limit: int = 100) -> Dict[str, Any]:
        """Sincroniza logs de asistencia del panel inBIO"""
        try:
            device = InBIODevice(device_ip)
            if not device.connect():
                return {"success": False, "message": "No se pudo conectar al panel"}
            
            try:
                # Obtener logs del panel
                logs = device.get_attendance_logs(limit)
                
                synced_count = 0
                for log in logs:
                    # Verificar si el log ya existe
                    existing_event = self.db.query(AccessEvent).filter(
                        AccessEvent.user_id == log.get("user_id"),
                        AccessEvent.event_time == log.get("timestamp")
                    ).first()
                    
                    if not existing_event:
                        # Crear nuevo evento
                        event = AccessEvent(
                            user_id=log.get("user_id"),
                            event_type=log.get("event_type", "access_granted"),
                            access_method="fingerprint",
                            access_granted=True,
                            device_ip=device_ip,
                            event_time=log.get("timestamp")
                        )
                        self.db.add(event)
                        synced_count += 1
                
                self.db.commit()
                
                return {
                    "success": True,
                    "message": f"Sincronizados {synced_count} logs de asistencia",
                    "synced_count": synced_count,
                    "total_logs": len(logs)
                }
                
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error sincronizando logs: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
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
    
    def get_device_status(self, device_ip: str) -> Dict[str, Any]:
        """Obtiene estado del panel inBIO"""
        try:
            device = InBIODevice(device_ip)
            if device.connect():
                info = device.get_device_info()
                device.disconnect()
                return {
                    "connected": True,
                    "device_info": info,
                    "message": "Panel inBIO conectado correctamente"
                }
            else:
                return {
                    "connected": False,
                    "message": "No se pudo conectar al panel inBIO"
                }
        except Exception as e:
            return {
                "connected": False,
                "message": f"Error: {str(e)}"
            }








