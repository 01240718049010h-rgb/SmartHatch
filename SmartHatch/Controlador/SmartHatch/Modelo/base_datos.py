import psycopg2
import os

DATABASE_URL = "postgresql://smarthatch_db_user:8zdKUU03sgVXqKfInHKKIkjIxyLqs1sx@dpg-d6t0phfgi27c73dctv6g-a.virginia-postgres.render.com/smarthatch_db"

def crear_base_datos():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("Conectado a PostgreSQL en la nube...")

        # 1. TABLA USUARIOS (La que ya tenías)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS USUARIOS (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                rol VARCHAR(20) NOT NULL,
                estudios VARCHAR(100),
                correo VARCHAR(100),
                ultima_conexion TIMESTAMP
            )
        ''')

        # === INSERTAR UN USUARIO ADMIN POR DEFECTO ===
        cursor.execute("SELECT COUNT(*) FROM USUARIOS")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO USUARIOS (usuario, password, nombre, rol, correo) 
                VALUES (%s, %s, %s, %s, %s)
            ''', ('admin', '1234', 'Super Administrador', 'admin', 'admin@smarthatch.com'))
            print("[!] Usuario por defecto creado: admin / 1234")

        # 2. NUEVA TABLA: HISTORIAL_SENSORES 🌡️💧
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS HISTORIAL_SENSORES (
                id SERIAL PRIMARY KEY,
                temperatura NUMERIC(5,2),
                humedad NUMERIC(5,2),
                distancia NUMERIC(5,2),
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[!] Tabla HISTORIAL_SENSORES verificada/creada.")

        # 3. NUEVA TABLA: LOTES 🥚
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LOTES (
                id SERIAL PRIMARY KEY,
                numero INTEGER NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estado VARCHAR(20) DEFAULT 'activo',
                dias_incubacion INTEGER DEFAULT 21
            )
        ''')
        
        # Add ultimo_volteo if it doesn't exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='lotes' and column_name='ultimo_volteo';
        """)
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE LOTES ADD COLUMN ultimo_volteo TIMESTAMP')
            print("[!] Columna ultimo_volteo agregada a LOTES.")
            
        print("[!] Tabla LOTES verificada/creada.")

        # 4. NUEVA TABLA: ESTADO_ACTUADORES ⚙️
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ESTADO_ACTUADORES (
                id SERIAL PRIMARY KEY,
                calefactor BOOLEAN DEFAULT false,
                ventilador BOOLEAN DEFAULT false,
                rotacion NUMERIC(5,2) DEFAULT 45.0
            )
        ''')
        
        # Insertar valores por defecto para los actuadores si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM ESTADO_ACTUADORES")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO ESTADO_ACTUADORES (calefactor, ventilador, rotacion) VALUES (false, false, 45.0)")
            print("[!] Estado inicial de actuadores configurado.")
        else:
            print("[!] Tabla ESTADO_ACTUADORES verificada.")

        # 5. NUEVA TABLA: HISTORIAL_ACCIONES 📜
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS HISTORIAL_ACCIONES (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL,
                accion VARCHAR(255) NOT NULL,
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[!] Tabla HISTORIAL_ACCIONES verificada/creada.")


        conn.commit()
        cursor.close()
        conn.close()
        print("¡Base de datos estructurada con éxito en PostgreSQL!")

    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")

if __name__ == '__main__':
    crear_base_datos()