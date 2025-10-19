import sys
import os

# Añadir el directorio raíz del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configurar la URL de la base de datos
os.environ["DATABASE_URL"] = "mysql+pymysql://root:123456@localhost/gym_db"

from app.core.database import Base, engine
from app.models.clinical_history import ClinicalHistory, UserGoal, MembershipPlan, HistoryType
from app.models.user import User
from app.models.membership import Membership

def create_clinical_tables():
    print("🚀 Creando tablas de historial clínico y planes de membresía...")
    try:
        # Asegúrate de que todos los modelos estén importados para que Base los registre
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente:")
        print("✅ Tabla 'clinical_histories' creada correctamente")
        print("✅ Tabla 'user_goals' creada correctamente") 
        print("✅ Tabla 'membership_plans' creada correctamente")
        
        # Crear algunos planes de membresía por defecto
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Verificar si ya existen planes
            existing_plans = db.query(MembershipPlan).count()
            
            if existing_plans == 0:
                print("📋 Creando planes de membresía por defecto...")
                
                plans = [
                    MembershipPlan(
                        name="Plan Básico Mensual",
                        description="Acceso completo al gimnasio durante un mes",
                        plan_type="monthly",
                        price=120000,
                        duration_days=30,
                        access_hours_start="06:00",
                        access_hours_end="22:00",
                        includes_trainer=False,
                        includes_nutritionist=False,
                        includes_pool=True,
                        includes_classes=True,
                        max_guests=0,
                        is_active=True,
                        is_popular=True
                    ),
                    MembershipPlan(
                        name="Plan Premium Mensual",
                        description="Acceso completo con entrenador personal y nutricionista",
                        plan_type="monthly",
                        price=200000,
                        discount_price=180000,
                        duration_days=30,
                        access_hours_start="05:00",
                        access_hours_end="23:00",
                        includes_trainer=True,
                        includes_nutritionist=True,
                        includes_pool=True,
                        includes_classes=True,
                        max_guests=2,
                        is_active=True,
                        is_popular=False
                    ),
                    MembershipPlan(
                        name="Acceso Diario",
                        description="Acceso por un día al gimnasio",
                        plan_type="daily",
                        price=15000,
                        duration_days=1,
                        access_hours_start="06:00",
                        access_hours_end="22:00",
                        includes_trainer=False,
                        includes_nutritionist=False,
                        includes_pool=False,
                        includes_classes=False,
                        max_guests=0,
                        is_active=True,
                        is_popular=False
                    ),
                    MembershipPlan(
                        name="Plan Estudiante",
                        description="Plan especial para estudiantes con descuento",
                        plan_type="monthly",
                        price=100000,
                        discount_price=80000,
                        duration_days=30,
                        access_hours_start="14:00",
                        access_hours_end="20:00",
                        includes_trainer=False,
                        includes_nutritionist=False,
                        includes_pool=True,
                        includes_classes=True,
                        max_guests=1,
                        is_active=True,
                        is_popular=False
                    )
                ]
                
                for plan in plans:
                    db.add(plan)
                
                db.commit()
                print(f"✅ {len(plans)} planes de membresía creados")
            else:
                print(f"ℹ️ Ya existen {existing_plans} planes de membresía")
                
        except Exception as e:
            print(f"❌ Error creando planes por defecto: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")

if __name__ == "__main__":
    create_clinical_tables()









