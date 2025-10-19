"""
Script para crear las tablas de huellas dactilares y control de acceso
"""
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.fingerprint import Fingerprint, AccessEvent, DeviceConfig
from app.models.user import User
from app.models.membership import Membership
from app.core.database import Base

def create_fingerprint_tables():
    """Crea las tablas necesarias para el sistema de huellas dactilares"""
    try:
        # Crear engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas de huellas dactilares creadas exitosamente")
        
        # Verificar que las tablas se crearon
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            required_tables = ['fingerprints', 'access_events', 'device_configs']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Tabla '{table}' creada correctamente")
                else:
                    print(f"❌ Error: Tabla '{table}' no se creó")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

if __name__ == "__main__":
    create_fingerprint_tables()









