from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import socket
import struct
import time
from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig, FingerprintStatus
from app.models.user import User
from app.models.membership import Membership, MembershipStatus
from app.core.database import get_db

logger = logging.getLogger(__name__)

class ZKTecoDevice:
    """Clase para comunicación con dispositivos ZKTeco"""
    
    def __init__(self, ip: str, port: int = 4370, timeout: int = 5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.session_id = 0
        self.reply_id = 0
        
    def connect(self) -> bool:
        """Conecta al dispositivo ZKTeco"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.ip, self.port))
            
            # Inicializar sesión
            response = self._send_command(1000, b'')
            if response and len(response) > 8:
                self.session_id = struct.unpack('<I', response[4:8])[0]
                logger.info(f"Conectado al dispositivo ZKTeco en {self.ip}:{self.port}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error conectando al dispositivo {self.ip}: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del dispositivo"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def _send_command(self, command: int, data: bytes) -> Optional[bytes]:
        """Envía comando al dispositivo"""
        if not self.socket:
            return None
            
        try:
            # Construir paquete
            length = len(data) + 8
            packet = struct.pack('<HHII', command, self.reply_id, self.session_id, length) + data
            
            # Enviar comando
            self.socket.send(packet)
            
            # Recibir respuesta
            response = self.socket.recv(1024)
            if len(response) >= 8:
                self.reply_id += 1
                return response
            return None
        except Exception as e:
            logger.error(f"Error enviando comando {command}: {e}")
            return None
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Obtiene lista de usuarios del dispositivo"""
        users = []
        try:
            response = self._send_command(8, b'')
            if response and len(response) > 8:
                # Procesar respuesta (simplificado)
                # En implementación real, necesitarías parsear el formato específico de ZKTeco
                pass
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
        return users
    
    def enroll_fingerprint(self, user_id: int, finger_index: int = 0) -> bool:
        """Inicia proceso de enrolamiento de huella"""
        try:
            # Comando para iniciar enrolamiento
            data = struct.pack('<II', user_id, finger_index)
            response = self._send_command(9, data)
            return response is not None
        except Exception as e:
            logger.error(f"Error iniciando enrolamiento: {e}")
            return False
    
    def verify_fingerprint(self, user_id: int) -> bool:
        """Verifica huella dactilar"""
        try:
            data = struct.pack('<I', user_id)
            response = self._send_command(10, data)
            return response is not None and len(response) > 8
        except Exception as e:
            logger.error(f"Error verificando huella: {e}")
            return False
    
    def open_door(self, relay_port: int = 1, duration: int = 5) -> bool:
        """Abre la talanquera/puerta"""
        try:
            data = struct.pack('<II', relay_port, duration)
            response = self._send_command(66, data)
            return response is not None
        except Exception as e:
            logger.error(f"Error abriendo puerta: {e}")
            return False


class FingerprintService:
    """Servicio para gestión de huellas dactilares y control de acceso"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def enroll_user_fingerprint(self, user_id: int, device_ip: str, finger_index: int = 0) -> Dict[str, Any]:
        """Enrola huella dactilar de usuario"""
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
            
            # Conectar al dispositivo
            device = ZKTecoDevice(device_ip)
            if not device.connect():
                return {"success": False, "message": "No se pudo conectar al dispositivo"}
            
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
                        "message": "Enrolamiento iniciado. Coloque el dedo en el sensor.",
                        "fingerprint_id": fingerprint.id
                    }
                else:
                    return {"success": False, "message": "Error iniciando enrolamiento"}
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error en enrolamiento: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}
    
    def verify_access(self, device_ip: str, user_id: int = None) -> Dict[str, Any]:
        """Verifica acceso basado en huella dactilar y membresía"""
        try:
            # Conectar al dispositivo
            device = ZKTecoDevice(device_ip)
            if not device.connect():
                return {
                    "access_granted": False,
                    "reason": "device_connection_error",
                    "message": "No se pudo conectar al dispositivo"
                }
            
            try:
                # Si no se proporciona user_id, el dispositivo debería devolverlo
                if not user_id:
                    # En implementación real, el dispositivo devolvería el user_id
                    # Por ahora, simulamos que se obtiene del dispositivo
                    user_id = self._get_user_from_device(device)
                
                if not user_id:
                    return {
                        "access_granted": False,
                        "reason": "user_not_found",
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
                
                # Verificar huella dactilar
                fingerprint = self.db.query(Fingerprint).filter(
                    Fingerprint.user_id == user_id,
                    Fingerprint.status == FingerprintStatus.ACTIVE
                ).first()
                
                if not fingerprint:
                    self._log_access_event(user_id, None, "access_denied", "no_fingerprint", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "no_fingerprint",
                        "message": "Usuario no tiene huella registrada"
                    }
                
                # Verificar huella en dispositivo
                if device.verify_fingerprint(user_id):
                    # Abrir talanquera
                    if device.open_door():
                        # Actualizar último uso de huella
                        fingerprint.last_used = datetime.now()
                        self.db.commit()
                        
                        # Registrar evento de acceso exitoso
                        self._log_access_event(user_id, fingerprint.id, "access_granted", None, device_ip)
                        
                        return {
                            "access_granted": True,
                            "user": user.name,
                            "membership": active_membership.membership_type,
                            "message": "Acceso autorizado"
                        }
                    else:
                        self._log_access_event(user_id, fingerprint.id, "access_denied", "door_error", device_ip)
                        return {
                            "access_granted": False,
                            "reason": "door_error",
                            "message": "Error abriendo talanquera"
                        }
                else:
                    self._log_access_event(user_id, fingerprint.id, "access_denied", "invalid_fingerprint", device_ip)
                    return {
                        "access_granted": False,
                        "reason": "invalid_fingerprint",
                        "message": "Huella dactilar no coincide"
                    }
                    
            finally:
                device.disconnect()
                
        except Exception as e:
            logger.error(f"Error verificando acceso: {e}")
            return {
                "access_granted": False,
                "reason": "system_error",
                "message": f"Error interno: {str(e)}"
            }
    
    def _get_user_from_device(self, device: ZKTecoDevice) -> Optional[int]:
        """Obtiene user_id del dispositivo (implementación simplificada)"""
        # En implementación real, esto dependería del protocolo específico del dispositivo
        # Por ahora retornamos None para que se maneje externamente
        return None
    
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
    
    def get_user_fingerprints(self, user_id: int) -> List[Fingerprint]:
        """Obtiene huellas dactilares de un usuario"""
        return self.db.query(Fingerprint).filter(
            Fingerprint.user_id == user_id
        ).all()
    
    def delete_fingerprint(self, fingerprint_id: int) -> bool:
        """Elimina huella dactilar"""
        try:
            fingerprint = self.db.query(Fingerprint).filter(
                Fingerprint.id == fingerprint_id
            ).first()
            
            if fingerprint:
                self.db.delete(fingerprint)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando huella: {e}")
            return False
    
    def get_access_events(self, user_id: Optional[int] = None, 
                         limit: int = 100) -> List[AccessEvent]:
        """Obtiene eventos de acceso"""
        query = self.db.query(AccessEvent)
        
        if user_id:
            query = query.filter(AccessEvent.user_id == user_id)
        
        return query.order_by(AccessEvent.event_time.desc()).limit(limit).all()








