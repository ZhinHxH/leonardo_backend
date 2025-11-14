#!/usr/bin/env python3
"""
Script de migración para agregar campos de descuento faltantes a la tabla sales
"""

import sys
import os
from sqlalchemy import text

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine, SessionLocal

def print_header(title: str):
    """Imprime un encabezado formateado"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_success(message: str):
    """Imprime un mensaje de éxito"""
    print(f"✅ {message}")

def print_info(message: str):
    """Imprime un mensaje informativo"""
    print(f"ℹ️  {message}")

def print_error(message: str):
    """Imprime un mensaje de error"""
    print(f"❌ {message}")

def check_table_exists():
    """Verifica si la tabla sales existe"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'sales'
            """))
            count = result.fetchone()[0]
            return count > 0
    except Exception as e:
        print_error(f"Error verificando tabla sales: {e}")
        return False

def check_column_exists(column_name: str):
    """Verifica si una columna existe en la tabla sales"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'sales' 
                AND column_name = :column_name
            """), {"column_name": column_name})
            count = result.fetchone()[0]
            return count > 0
    except Exception as e:
        print_error(f"Error verificando columna {column_name}: {e}")
        return False

def add_discount_columns():
    """Agrega las columnas de descuento faltantes a la tabla sales"""
    print_header("AGREGANDO CAMPOS DE DESCUENTO A LA TABLA SALES")
    
    try:
        # Verificar si la tabla sales existe
        if not check_table_exists():
            print_error("La tabla 'sales' no existe. Ejecute primero el script de instalación de esquemas.")
            return False
        
        # Lista de columnas a agregar
        columns_to_add = [
            {
                "name": "is_discount",
                "definition": "BOOLEAN DEFAULT FALSE NOT NULL",
                "description": "Indica si la venta tiene descuento aplicado"
            },
            {
                "name": "discount_reason", 
                "definition": "VARCHAR(100) DEFAULT NULL",
                "description": "Razón del descuento aplicado"
            },
            {
                "name": "discount_amount",
                "definition": "FLOAT DEFAULT 0.0 NOT NULL",
                "description": "Monto del descuento aplicado"
            }
        ]
        
        added_count = 0
        
        with engine.connect() as conn:
            # Iniciar transacción
            trans = conn.begin()
            
            try:
                for column in columns_to_add:
                    column_name = column["name"]
                    column_definition = column["definition"]
                    description = column["description"]
                    
                    # Verificar si la columna ya existe
                    if check_column_exists(column_name):
                        print_info(f"La columna '{column_name}' ya existe")
                        continue
                    
                    # Agregar la columna
                    alter_sql = f"ALTER TABLE sales ADD COLUMN {column_name} {column_definition}"
                    conn.execute(text(alter_sql))
                    
                    print_success(f"Columna '{column_name}' agregada: {description}")
                    added_count += 1
                
                # Confirmar transacción
                trans.commit()
                
                if added_count > 0:
                    print_success(f"{added_count} columnas agregadas exitosamente")
                else:
                    print_info("Todas las columnas ya existen")
                
                return True
                
            except Exception as e:
                # Revertir transacción en caso de error
                trans.rollback()
                raise e
                
    except Exception as e:
        print_error(f"Error agregando columnas: {e}")
        return False

def verify_migration():
    """Verifica que la migración se haya aplicado correctamente"""
    print_header("VERIFICANDO MIGRACIÓN")
    
    try:
        required_columns = ["is_discount", "discount_reason", "discount_amount"]
        missing_columns = []
        
        for column in required_columns:
            if not check_column_exists(column):
                missing_columns.append(column)
        
        if missing_columns:
            print_error(f"Columnas faltantes: {', '.join(missing_columns)}")
            return False
        else:
            print_success("Todas las columnas de descuento están presentes")
            return True
            
    except Exception as e:
        print_error(f"Error verificando migración: {e}")
        return False

def main():
    """Función principal del script de migración"""
    print_header("MIGRACIÓN DE CAMPOS DE DESCUENTO - TABLA SALES")
    print("Este script agregará los campos de descuento faltantes a la tabla sales")
    
    # Paso 1: Agregar columnas
    if not add_discount_columns():
        print_error("Error en la migración. Abortando.")
        return False
    
    # Paso 2: Verificar migración
    if not verify_migration():
        print_error("La verificación de migración falló.")
        return False
    
    print_header("MIGRACIÓN COMPLETADA")
    print_success("¡Los campos de descuento han sido agregados exitosamente!")
    print_info("Ahora puede ejecutar el script de instalación de esquemas sin errores")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)



