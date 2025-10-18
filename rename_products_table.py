import sys
import os
from sqlalchemy import create_engine, text

# Configurar la URL de la base de datos
DATABASE_URL = "mysql+pymysql://root:123456@localhost/gym_db"

def rename_products_table():
    """Renombra la tabla products_new a products para que coincida con el modelo"""
    print("🔧 Renombrando tabla products_new a products...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Verificar si existe products_new
            result = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'gym_db' 
                AND table_name = 'products_new'
            """)).fetchone()
            
            if result.count == 0:
                print("❌ La tabla products_new no existe. Ejecuta primero create_inventory_simple.py")
                return False
            
            # Verificar si existe products antigua
            result_old = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'gym_db' 
                AND table_name = 'products'
            """)).fetchone()
            
            if result_old.count > 0:
                print("📋 Renombrando tabla products antigua...")
                connection.execute(text("RENAME TABLE products TO products_backup"))
                connection.commit()
                print("✅ Tabla products renombrada a products_backup")
            
            # Renombrar products_new a products
            print("📋 Renombrando products_new a products...")
            connection.execute(text("RENAME TABLE products_new TO products"))
            connection.commit()
            print("✅ Tabla products_new renombrada a products")
            
            # Verificar que la tabla existe
            result_final = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'gym_db' 
                AND table_name = 'products'
            """)).fetchone()
            
            if result_final.count > 0:
                print("✅ Tabla products existe y está lista")
                
                # Mostrar algunos productos de ejemplo
                products = connection.execute(text("SELECT id, name, selling_price, current_stock FROM products LIMIT 3")).fetchall()
                print("📦 Productos de ejemplo:")
                for product in products:
                    print(f"   - {product.name}: ${product.selling_price:,.0f} (Stock: {product.current_stock})")
                
                return True
            else:
                print("❌ Error: La tabla products no existe después del renombrado")
                return False
            
    except Exception as e:
        print(f"❌ Error renombrando tabla: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if rename_products_table():
        print("🎉 Renombrado completado exitosamente")
        print("🚀 Ahora puedes usar el inventario desde el frontend")
    else:
        print("❌ Falló el renombrado de la tabla")








