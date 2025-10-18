from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

from app.models.clinical_history import ClinicalHistory, UserGoal, RecordType
from app.models.user import User
from app.core.logging_config import main_logger, exception_handler

logger = main_logger

class ClinicalHistoryService:
    """Servicio para gestionar historias clínicas"""

    def __init__(self, db: Session):
        self.db = db

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "get_user_history"})
    def get_user_history(self, user_id: int, record_type: Optional[str] = None) -> List[ClinicalHistory]:
        """Obtiene la historia clínica de un usuario"""
        
        query = self.db.query(ClinicalHistory).filter(ClinicalHistory.user_id == user_id)
        
        if record_type:
            # Validar que el tipo de registro sea válido
            valid_types = [e.value for e in RecordType]
            if record_type in valid_types:
                query = query.filter(ClinicalHistory.record_type == record_type)
            else:
                logger.warning(f"Tipo de registro inválido: {record_type}")
        
        records = query.order_by(desc(ClinicalHistory.record_date)).all()
        
        logger.info(f"Historia clínica obtenida para usuario {user_id}: {len(records)} registros")
        return records

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "create_record"})
    def create_record(self, record_data: Dict[str, Any], created_by_id: int) -> ClinicalHistory:
        """Crea un nuevo registro en la historia clínica"""
        
        # Validar que el usuario existe
        user = self.db.query(User).filter(User.id == record_data['user_id']).first()
        if not user:
            raise ValueError(f"Usuario con ID {record_data['user_id']} no encontrado")
        
        # Validar tipo de registro
        valid_types = [e.value for e in RecordType]
        if record_data['record_type'] not in valid_types:
            raise ValueError(f"Tipo de registro inválido: {record_data['record_type']}")
        
        # Crear el registro
        new_record = ClinicalHistory(
            user_id=record_data['user_id'],
            record_type=record_data['record_type'],
            weight=record_data.get('weight'),
            height=record_data.get('height'),
            body_fat=record_data.get('body_fat'),
            muscle_mass=record_data.get('muscle_mass'),
            measurements=record_data.get('measurements'),
            notes=record_data['notes'],
            recommendations=record_data.get('recommendations'),
            target_weight=record_data.get('target_weight'),
            target_body_fat=record_data.get('target_body_fat'),
            record_date=record_data.get('record_date', datetime.utcnow()),
            created_by_id=created_by_id
        )
        
        self.db.add(new_record)
        self.db.commit()
        self.db.refresh(new_record)
        
        logger.info(f"Registro clínico creado: ID {new_record.id} para usuario {record_data['user_id']}")
        return new_record

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "update_record"})
    def update_record(self, record_id: int, record_data: Dict[str, Any], updated_by_id: int) -> Optional[ClinicalHistory]:
        """Actualiza un registro de historia clínica"""
        
        record = self.db.query(ClinicalHistory).filter(ClinicalHistory.id == record_id).first()
        if not record:
            return None
        
        # Actualizar campos si se proporcionan
        for field, value in record_data.items():
            if hasattr(record, field) and value is not None:
                if field == 'record_type':
                    # Validar tipo de registro
                    valid_types = [e.value for e in RecordType]
                    if value not in valid_types:
                        raise ValueError(f"Tipo de registro inválido: {value}")
                    setattr(record, field, value)
                else:
                    setattr(record, field, value)
        
        record.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"Registro clínico actualizado: ID {record_id}")
        return record

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "delete_record"})
    def delete_record(self, record_id: int) -> bool:
        """Elimina un registro de historia clínica"""
        
        record = self.db.query(ClinicalHistory).filter(ClinicalHistory.id == record_id).first()
        if not record:
            return False
        
        self.db.delete(record)
        self.db.commit()
        
        logger.info(f"Registro clínico eliminado: ID {record_id}")
        return True

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "get_user_stats"})
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas del usuario basadas en su historia clínica"""
        
        records = self.db.query(ClinicalHistory).filter(
            ClinicalHistory.user_id == user_id
        ).order_by(ClinicalHistory.record_date).all()
        
        if not records:
            return {
                "total_records": 0,
                "first_record_date": None,
                "last_record_date": None,
                "weight_progress": [],
                "body_fat_progress": [],
                "muscle_mass_progress": []
            }
        
        # Calcular progreso de peso
        weight_progress = []
        body_fat_progress = []
        muscle_mass_progress = []
        
        for record in records:
            date_str = record.record_date.isoformat()
            
            if record.weight:
                weight_progress.append({
                    "date": date_str,
                    "value": record.weight,
                    "type": record.record_type.value
                })
            
            if record.body_fat:
                body_fat_progress.append({
                    "date": date_str,
                    "value": record.body_fat,
                    "type": record.record_type.value
                })
            
            if record.muscle_mass:
                muscle_mass_progress.append({
                    "date": date_str,
                    "value": record.muscle_mass,
                    "type": record.record_type.value
                })
        
        # Estadísticas básicas
        stats = {
            "total_records": len(records),
            "first_record_date": records[0].record_date.isoformat(),
            "last_record_date": records[-1].record_date.isoformat(),
            "weight_progress": weight_progress,
            "body_fat_progress": body_fat_progress,
            "muscle_mass_progress": muscle_mass_progress
        }
        
        # Calcular cambios si hay datos suficientes
        if len(weight_progress) >= 2:
            weight_change = weight_progress[-1]["value"] - weight_progress[0]["value"]
            stats["weight_change"] = weight_change
        
        if len(body_fat_progress) >= 2:
            body_fat_change = body_fat_progress[-1]["value"] - body_fat_progress[0]["value"]
            stats["body_fat_change"] = body_fat_change
        
        if len(muscle_mass_progress) >= 2:
            muscle_change = muscle_mass_progress[-1]["value"] - muscle_mass_progress[0]["value"]
            stats["muscle_mass_change"] = muscle_change
        
        logger.info(f"Estadísticas calculadas para usuario {user_id}")
        return stats

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "create_goal"})
    def create_goal(self, goal_data: Dict[str, Any], created_by_id: int) -> UserGoal:
        """Crea un nuevo objetivo para el usuario"""
        
        # Validar que el usuario existe
        user = self.db.query(User).filter(User.id == goal_data['user_id']).first()
        if not user:
            raise ValueError(f"Usuario con ID {goal_data['user_id']} no encontrado")
        
        # Crear el objetivo
        new_goal = UserGoal(
            user_id=goal_data['user_id'],
            target_weight=goal_data.get('target_weight'),
            target_body_fat=goal_data.get('target_body_fat'),
            target_muscle_mass=goal_data.get('target_muscle_mass'),
            target_date=goal_data.get('target_date'),
            description=goal_data['description'],
            notes=goal_data.get('notes'),
            created_by_id=created_by_id
        )
        
        self.db.add(new_goal)
        self.db.commit()
        self.db.refresh(new_goal)
        
        logger.info(f"Objetivo creado: ID {new_goal.id} para usuario {goal_data['user_id']}")
        return new_goal

    @exception_handler(logger, {"service": "ClinicalHistoryService", "method": "get_user_goals"})
    def get_user_goals(self, user_id: int, active_only: bool = True) -> List[UserGoal]:
        """Obtiene los objetivos de un usuario"""
        
        query = self.db.query(UserGoal).filter(UserGoal.user_id == user_id)
        
        if active_only:
            query = query.filter(UserGoal.is_active == True)
        
        goals = query.order_by(desc(UserGoal.created_at)).all()
        
        logger.info(f"Objetivos obtenidos para usuario {user_id}: {len(goals)} objetivos")
        return goals