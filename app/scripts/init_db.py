#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos básicos
"""

import sys
import os
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine, SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.core.config import settings

def create_admin_user():
    """Crea un usuario administrador por defecto"""
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # Verificar si ya existe un usuario admin
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_user:
            print("✅ Usuario administrador ya existe")
            return
        
        # Crear hash de la contraseña
        password_hash = auth_service.get_password_hash("admin123")
        
        # Crear usuario administrador
        admin_user = User(
            email="admin@gym.com",
            password_hash=password_hash,
            name="Administrador del Sistema",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ Usuario administrador creado exitosamente")
        print("📧 Email: admin@gym.com")
        print("🔑 Contraseña: admin123")
        
    except Exception as e:
        print(f"❌ Error creando usuario administrador: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_users():
    """Crea usuarios de ejemplo para diferentes roles"""
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # Usuarios de ejemplo
        sample_users = [
            {
                "email": "manager@gym.com",
                "password": "manager123",
                "name": "Gerente del Gimnasio",
                "role": UserRole.MANAGER
            },
            {
                "email": "trainer@gym.com",
                "password": "trainer123",
                "name": "Entrenador Principal",
                "role": UserRole.TRAINER
            },
            {
                "email": "receptionist@gym.com",
                "password": "reception123",
                "name": "Recepcionista",
                "role": UserRole.RECEPTIONIST
            },
            {
                "email": "member@gym.com",
                "password": "member123",
                "name": "Miembro Ejemplo",
                "role": UserRole.MEMBER
            }
        ]
        
        created_count = 0
        for user_data in sample_users:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                continue
            
            # Crear hash de la contraseña
            password_hash = auth_service.get_password_hash(user_data["password"])
            
            # Crear usuario
            user = User(
                email=user_data["email"],
                password_hash=password_hash,
                name=user_data["name"],
                role=user_data["role"],
                is_active=True
            )
            
            db.add(user)
            created_count += 1
        
        db.commit()
        
        if created_count > 0:
            print(f"✅ {created_count} usuarios de ejemplo creados")
        else:
            print("ℹ️  Los usuarios de ejemplo ya existen")
            
    except Exception as e:
        print(f"❌ Error creando usuarios de ejemplo: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Función principal del script"""
    print("🚀 Inicializando base de datos...")
    
    # Crear usuario administrador
    create_admin_user()
    
    # Crear usuarios de ejemplo
    create_sample_users()
    
    print("✅ Inicialización completada")
    print("\n📋 Credenciales de acceso:")
    print("👤 Admin: admin@gym.com / admin123")
    print("👤 Manager: manager@gym.com / manager123")
    print("👤 Trainer: trainer@gym.com / trainer123")
    print("👤 Receptionist: receptionist@gym.com / reception123")
    print("👤 Member: member@gym.com / member123")

if __name__ == "__main__":
    main()





