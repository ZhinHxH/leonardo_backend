from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class UserService:
    """Servicio para gestión de usuarios"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @exception_handler(logger, {"service": "UserService", "method": "get_users"})
    def get_users(self, 
                 search: Optional[str] = None,
                 skip: int = 0,
                 limit: int = 100,
                 role: Optional[str] = None,
                 is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Obtiene lista de usuarios con filtros"""
        
        query = self.db.query(User)
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.dni.ilike(search_term),
                    User.phone.ilike(search_term)
                )
            )
        
        if role:
            query = query.filter(User.role == role)
            
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Contar total
        total_count = query.count()
        
        # Aplicar paginación y ordenar
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "users": users,
            "total": total_count
        }

    @exception_handler(logger, {"service": "UserService", "method": "create_user"})
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Crea un nuevo usuario"""
        
        # Verificar si el email ya existe
        existing_user = self.db.query(User).filter(User.email == user_data['email']).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si el DNI ya existe (si se proporciona)
        if user_data.get('dni'):
            existing_dni = self.db.query(User).filter(User.dni == user_data['dni']).first()
            if existing_dni:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El DNI ya está registrado"
                )
        
        # Hashear contraseña
        hashed_password = self.pwd_context.hash(user_data['password'])
        
        # Convertir fecha de nacimiento si se proporciona
        birth_date = None
        if user_data.get('birth_date'):
            try:
                from datetime import datetime
                birth_date = datetime.strptime(user_data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {user_data['birth_date']}")
        
        # Crear usuario
        new_user = User(
            name=user_data['name'],
            email=user_data['email'],
            password_hash=hashed_password,
            dni=user_data.get('dni'),
            phone=user_data.get('phone'),
            role=user_data.get('role', UserRole.MEMBER),
            address=user_data.get('address'),
            birth_date=birth_date,
            blood_type=user_data.get('blood_type'),
            gender=user_data.get('gender'),
            eps=user_data.get('eps'),
            emergency_contact=user_data.get('emergency_contact'),
            emergency_phone=user_data.get('emergency_phone'),
            is_active=True
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"✅ Usuario creado: {new_user.email}")
        return new_user

    @exception_handler(logger, {"service": "UserService", "method": "get_user_by_id"})
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    @exception_handler(logger, {"service": "UserService", "method": "update_user"})
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Actualiza un usuario existente"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Verificar email único si se está cambiando
        if 'email' in user_data and user_data['email'] != user.email:
            existing_email = self.db.query(User).filter(
                User.email == user_data['email'],
                User.id != user_id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado"
                )
        
        # Verificar DNI único si se está cambiando
        if 'dni' in user_data and user_data['dni'] and user_data['dni'] != user.dni:
            existing_dni = self.db.query(User).filter(
                User.dni == user_data['dni'],
                User.id != user_id
            ).first()
            if existing_dni:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El DNI ya está registrado"
                )
        
        # Actualizar campos
        for key, value in user_data.items():
            if key == 'password' and value:
                # Hashear nueva contraseña
                user.password_hash = self.pwd_context.hash(value)
            elif hasattr(user, key) and key != 'password':
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"✅ Usuario actualizado: {user.email}")
        return user

    @exception_handler(logger, {"service": "UserService", "method": "delete_user"})
    def delete_user(self, user_id: int) -> bool:
        """Elimina un usuario"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # No permitir eliminar admin si es el único
        if user.role == 'admin':
            admin_count = self.db.query(User).filter(User.role == 'admin').count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar el último administrador"
                )
        
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"✅ Usuario eliminado: {user.email}")
        return True

    @exception_handler(logger, {"service": "UserService", "method": "search_customers"})
    def search_customers(self, search: Optional[str] = None, limit: int = 50) -> List[User]:
        """Busca clientes (usuarios con rol member) para autocompletado"""
        
        query = self.db.query(User).filter(User.role == 'member', User.is_active == True)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.dni.ilike(search_term),
                    User.phone.ilike(search_term)
                )
            )
        
        return query.order_by(User.name).limit(limit).all()

    @exception_handler(logger, {"service": "UserService", "method": "get_user_stats"})
    def get_user_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de usuarios"""
        
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        
        # Usuarios por rol
        role_stats = self.db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        role_counts = {role: count for role, count in role_stats}
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts
        }