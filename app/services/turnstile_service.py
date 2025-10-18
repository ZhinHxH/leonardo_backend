from typing import Optional, Dict, Any
import serial
import socket
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class TurnstileController:
    """Controlador para comunicación con talanquera"""
    
    def __init__(self, connection_type: str = "serial", **kwargs):
        self.connection_type = connection_type
        self.connection = None
        self.is_connected = False
        
        if connection_type == "serial":
            self.port = kwargs.get("port", "COM1")
            self.baudrate = kwargs.get("baudrate", 9600)
        elif connection_type == "tcp":
            self.host = kwargs.get("host", "192.168.1.100")
            self.port = kwargs.get("port", 8080)
        elif connection_type == "relay":
            self.relay_ip = kwargs.get("relay_ip", "192.168.1.101")
            self.relay_port = kwargs.get("relay_port", 1)
    
    def connect(self) -> bool:
        """Conecta a la talanquera"""
        try:
            if self.connection_type == "serial":
                self.connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=1
                )
                self.is_connected = True
                logger.info(f"Conectado a talanquera por puerto serie {self.port}")
                
            elif self.connection_type == "tcp":
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.host, self.port))
                self.is_connected = True
                logger.info(f"Conectado a talanquera por TCP {self.host}:{self.port}")
                
            elif self.connection_type == "relay":
                # Para relés IP, no necesitamos mantener conexión abierta
                self.is_connected = True
                logger.info(f"Configurado para control por relé IP {self.relay_ip}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a talanquera: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Desconecta de la talanquera"""
        if self.connection:
            try:
                if self.connection_type in ["serial", "tcp"]:
                    self.connection.close()
            except:
                pass
            self.connection = None
        self.is_connected = False
    
    def open_turnstile(self, duration: int = 5) -> bool:
        """Abre la talanquera por un tiempo determinado"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return False
            
            if self.connection_type == "serial":
                # Comando para abrir talanquera (ajustar según protocolo)
                command = f"OPEN:{duration}\n".encode()
                self.connection.write(command)
                response = self.connection.readline().decode().strip()
                return "OK" in response
                
            elif self.connection_type == "tcp":
                # Comando TCP para abrir talanquera
                command = f"OPEN:{duration}\n"
                self.connection.send(command.encode())
                response = self.connection.recv(1024).decode().strip()
                return "OK" in response
                
            elif self.connection_type == "relay":
                # Control por relé IP
                return self._control_relay(True, duration)
            
            return False
            
        except Exception as e:
            logger.error(f"Error abriendo talanquera: {e}")
            return False
    
    def close_turnstile(self) -> bool:
        """Cierra la talanquera"""
        try:
            if not self.is_connected:
                return False
            
            if self.connection_type == "serial":
                command = "CLOSE\n".encode()
                self.connection.write(command)
                response = self.connection.readline().decode().strip()
                return "OK" in response
                
            elif self.connection_type == "tcp":
                command = "CLOSE\n"
                self.connection.send(command.encode())
                response = self.connection.recv(1024).decode().strip()
                return "OK" in response
                
            elif self.connection_type == "relay":
                return self._control_relay(False, 0)
            
            return False
            
        except Exception as e:
            logger.error(f"Error cerrando talanquera: {e}")
            return False
    
    def _control_relay(self, activate: bool, duration: int = 0) -> bool:
        """Controla relé IP para talanquera"""
        try:
            import requests
            
            # URL del relé IP (ajustar según modelo)
            url = f"http://{self.relay_ip}/relay/{self.relay_port}"
            
            if activate:
                # Activar relé
                response = requests.get(f"{url}/on", timeout=5)
                if response.status_code == 200 and duration > 0:
                    # Programar desactivación automática
                    time.sleep(duration)
                    requests.get(f"{url}/off", timeout=5)
                return response.status_code == 200
            else:
                # Desactivar relé
                response = requests.get(f"{url}/off", timeout=5)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error controlando relé: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado de la talanquera"""
        try:
            if not self.is_connected:
                return {
                    "connected": False,
                    "status": "disconnected",
                    "message": "No conectado"
                }
            
            if self.connection_type == "serial":
                # Enviar comando de estado
                command = "STATUS\n".encode()
                self.connection.write(command)
                response = self.connection.readline().decode().strip()
                
                return {
                    "connected": True,
                    "status": "connected",
                    "response": response,
                    "message": "Conectado por puerto serie"
                }
                
            elif self.connection_type == "tcp":
                command = "STATUS\n"
                self.connection.send(command.encode())
                response = self.connection.recv(1024).decode().strip()
                
                return {
                    "connected": True,
                    "status": "connected",
                    "response": response,
                    "message": "Conectado por TCP"
                }
                
            elif self.connection_type == "relay":
                return {
                    "connected": True,
                    "status": "connected",
                    "message": "Control por relé IP configurado"
                }
            
            return {
                "connected": False,
                "status": "unknown",
                "message": "Tipo de conexión no reconocido"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {
                "connected": False,
                "status": "error",
                "message": f"Error: {str(e)}"
            }


class TurnstileService:
    """Servicio para gestión de talanquera"""
    
    def __init__(self, connection_type: str = "relay", **kwargs):
        self.controller = TurnstileController(connection_type, **kwargs)
        self.last_access_time = None
        self.access_count = 0
    
    def grant_access(self, user_name: str, duration: int = 5) -> Dict[str, Any]:
        """Concede acceso abriendo la talanquera"""
        try:
            # Abrir talanquera
            success = self.controller.open_turnstile(duration)
            
            if success:
                self.last_access_time = datetime.now()
                self.access_count += 1
                
                logger.info(f"Acceso concedido a {user_name} - Talanquera abierta por {duration}s")
                
                return {
                    "success": True,
                    "message": f"Acceso concedido a {user_name}",
                    "duration": duration,
                    "timestamp": self.last_access_time.isoformat()
                }
            else:
                logger.error(f"Error concediendo acceso a {user_name}")
                return {
                    "success": False,
                    "message": "Error abriendo talanquera",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error en servicio de talanquera: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def deny_access(self, user_name: str, reason: str) -> Dict[str, Any]:
        """Niega acceso (no abre la talanquera)"""
        logger.info(f"Acceso denegado a {user_name} - Razón: {reason}")
        
        return {
            "success": False,
            "message": f"Acceso denegado a {user_name}",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del servicio de talanquera"""
        controller_status = self.controller.get_status()
        
        return {
            **controller_status,
            "last_access_time": self.last_access_time.isoformat() if self.last_access_time else None,
            "access_count": self.access_count
        }
    
    def test_connection(self) -> bool:
        """Prueba la conexión con la talanquera"""
        return self.controller.connect()








