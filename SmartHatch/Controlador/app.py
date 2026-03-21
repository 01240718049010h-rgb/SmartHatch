from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import psycopg2.extras
import random
import string
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ==========================================
# CONFIGURACIÓN
# ==========================================

# Define folders relative to this script's location
base_dir = os.path.dirname(os.path.abspath(__file__))
vista_dir = os.path.join(base_dir, '..', 'Vista')

app = Flask(__name__,
            template_folder=os.path.join(vista_dir, 'templates'),
            static_folder=os.path.join(vista_dir, 'static'))

# Lee la llave secreta
app.secret_key = os.getenv('SECRET_KEY')
# Lee directamente la base de datos
DATABASE_URL = os.getenv('DATABASE_URL')

# =================================================================
def obtener_conexion():
    """Conexión a PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("SET timezone = 'America/Merida';")
    return conn

def enviar_correo_credenciales(correo_destino, nombre, usuario_gen, password_gen):
    # Ahora Python leerá los datos directamente desde el panel de Render
    remitente = os.getenv('EMAIL')
    password_app = os.getenv('PASSWORD')

    # Construimos el mensaje
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = correo_destino
    msg['Subject'] = "Bienvenido a Smart Hatch - Credenciales de Acceso"

    # El cuerpo del correo (HTML con diseño profesional)
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
            body {{
                margin: 0; padding: 0; font-family: 'Montserrat', Arial, sans-serif;
                background-color: #f4f7f6; color: #333;
            }}
            .container {{
                max-width: 600px; margin: 20px auto; background-color: #ffffff;
                border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .header {{ background-color: #0f2027; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: 2px; }}
            .header span {{ color: #00d2d3; }}
            .content {{ padding: 40px; line-height: 1.6; }}
            .content h2 {{ color: #0f2027; font-size: 22px; margin-top: 0; }}
            .credentials-box {{
                background-color: #f0fdfd; border: 1px solid #00d2d3;
                border-radius: 8px; padding: 20px; margin: 25px 0;
            }}
            .credential-item {{ margin: 10px 0; font-size: 16px; }}
            .credential-label {{ font-weight: 600; color: #555; width: 100px; display: inline-block; }}
            .credential-value {{
                font-family: monospace; background: #e0e0e0; padding: 2px 6px;
                border-radius: 4px; font-weight: bold; color: #0f2027;
            }}
            .btn {{
                display: inline-block; padding: 15px 30px; background-color: #00d2d3;
                color: #0f2027 !important; text-decoration: none; border-radius: 8px;
                font-weight: 800; text-transform: uppercase; font-size: 14px;
                transition: 0.3s; margin-top: 20px;
            }}
            .footer {{
                background-color: #f9f9f9; padding: 20px; text-align: center;
                font-size: 12px; color: #999; border-top: 1px solid #eeeeee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Smart<span>Hatch</span></h1>
            </div>
            <div class="content">
                <h2>¡Bienvenido, {nombre}!</h2>
                <p>Has sido registrado exitosamente en el sistema de monitoreo <strong>Smart Hatch</strong>. Estamos emocionados de tenerte a bordo.</p>
                <p>A continuación, se presentan tus credenciales de acceso seguras para ingresar al panel:</p>
                <div class="credentials-box">
                    <div class="credential-item">
                        <span class="credential-label">Usuario:</span>
                        <span class="credential-value">{usuario_gen}</span>
                    </div>
                    <div class="credential-item">
                        <span class="credential-label">Contraseña:</span>
                        <span class="credential-value">{password_gen}</span>
                    </div>
                </div>
                <p>Te recomendamos tener guardado tu usuario y contraseña.</p>
                <div style="text-align: center;">
                    <a href="https://smarthatch.onrender.com" class="btn">Acceder al Sistema</a>
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2026 Smart Hatch - Sistema de Incubación IOT.<br>
                Este es un correo automático, por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo_html, 'html'))

   try:
        # Nos conectamos a Google y le damos MÁXIMO 8 segundos para responder
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=8) 
        server.starttls() 
        server.login(remitente, password_app)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando correo (Cancelado para evitar caída): {e}")
        return False

def inicializar_tabla_lotes():
    """Crea la tabla LOTES si no existe."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LOTES (
                id SERIAL PRIMARY KEY,
                numero INTEGER NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estado VARCHAR(20) DEFAULT 'activo',
                dias_incubacion INTEGER DEFAULT 21
            )
        ''')
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al crear tabla LOTES: {e}")
    finally:
        if conn is not None:
            conn.close()

def inicializar_tabla_actuadores():
    """Crea la tabla ESTADO_ACTUADORES con valores por defecto."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ESTADO_ACTUADORES (
                id SERIAL PRIMARY KEY,
                calefactor BOOLEAN DEFAULT false,
                ventilador BOOLEAN DEFAULT false,
                rotacion NUMERIC(5,2) DEFAULT 45.0
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM ESTADO_ACTUADORES")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO ESTADO_ACTUADORES (calefactor, ventilador, rotacion) VALUES (false, false, 45.0)")
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al crear tabla ESTADO_ACTUADORES: {e}")
    finally:
        if conn is not None:
            conn.close()

def inicializar_tabla_acciones():
    """Crea la tabla HISTORIAL_ACCIONES si no existe."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS HISTORIAL_ACCIONES (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL,
                accion VARCHAR(255) NOT NULL,
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al crear tabla HISTORIAL_ACCIONES: {e}")
    finally:
        if conn is not None:
            conn.close()

def registrar_accion(usuario, accion):
    """Registra una acción en el historial de forma global."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO HISTORIAL_ACCIONES (usuario, accion) VALUES (%s, %s)',
            (usuario, accion)
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al registrar acción: {e}")
    finally:
        if conn is not None:
            conn.close()

inicializar_tabla_lotes()
inicializar_tabla_actuadores()
inicializar_tabla_acciones()

# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================

@app.route('/')
def index():
    if 'usuario' in session:
        if session['rol'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def procesar_login():
    usuario_form = request.form['usuario']
    password_form = request.form['password']
    rol_form = request.form['rol']

    conn = None
    user = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM USUARIOS WHERE usuario = %s AND password = %s', (usuario_form, password_form))
        user = cursor.fetchone()
        cursor.close()
    except Exception as e:
        flash('Error al conectar con la base de datos.')
        return redirect(url_for('index'))
    finally:
        if conn is not None:
            conn.close()

    if user:
        rol_bd = user['rol']
        if (rol_form == 'supervisor' and rol_bd == 'admin') or (rol_form == 'investigador' and rol_bd == 'investigador'):
            # === NUEVO: Actualizar última conexión ===
            conn_upd = None
            try:
                conn_upd = obtener_conexion()
                cursor_upd = conn_upd.cursor()
                cursor_upd.execute('UPDATE USUARIOS SET ultima_conexion = CURRENT_TIMESTAMP WHERE id = %s', (user['id'],))
                conn_upd.commit()
                cursor_upd.close()
            except Exception as e:
                print(f"Error al actualizar ultima_conexion: {e}")
            finally:
                if conn_upd is not None:
                    conn_upd.close()

            session['id'] = user['id']
            session['usuario'] = user['usuario']
            session['nombre'] = user['nombre']
            session['rol'] = rol_bd

            registrar_accion(user['nombre'], 'Inició sesión')
            
            if rol_bd == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Error: El rol seleccionado no coincide con tus credenciales.')
            return redirect(url_for('index'))
    else:
        flash('Error: Usuario o contraseña incorrectos.')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if 'nombre' in session:
        registrar_accion(session['nombre'], 'Cerró sesión')
    session.clear()
    return redirect(url_for('index'))

@app.route('/autores')
def autores():
    return render_template('autores.html')

@app.route('/informacion')
def informacion():
    return render_template('informacion.html')

# ==========================================
# PANEL DE ADMINISTRADOR
# ==========================================

@app.route('/admin')
def admin():
    if 'usuario' in session and session['rol'] == 'admin':
        conn = None
        try:
            conn = obtener_conexion()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('SELECT * FROM USUARIOS ORDER BY id DESC')
            lista_usuarios = cursor.fetchall()
            cursor.execute("SELECT * FROM LOTES ORDER BY numero ASC")
            lista_lotes = cursor.fetchall()
            cursor.execute("SELECT * FROM HISTORIAL_ACCIONES ORDER BY id DESC LIMIT 50")
            historial_acciones = cursor.fetchall()
            cursor.close()
            
            return render_template('panel-admin.html', nombre_usuario=session['nombre'], usuarios=lista_usuarios, lotes=lista_lotes, historial_acciones=historial_acciones)
        except Exception as e:
            flash(f'Error al cargar datos: {e}')
            return render_template('panel-admin.html', nombre_usuario=session['nombre'], usuarios=[], lotes=[], historial_acciones=[])
        finally:
            if conn is not None:
                conn.close()

    flash('Acceso denegado. Permisos de administrador requeridos.')
    return redirect(url_for('index'))

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    nombre = request.form['nombre']
    rol = request.form['rol']
    estudios = request.form['estudios']
    correo = request.form['correo']

    num_aleatorio = random.randint(1000, 9999)
    nuevo_usuario = f"U-{num_aleatorio}"
    nueva_password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Insertar en PostgreSQL
        cursor.execute('''
            INSERT INTO USUARIOS (usuario, password, nombre, rol, estudios, correo)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (nuevo_usuario, nueva_password, nombre, rol, estudios, correo))

        conn.commit()
        cursor.close()
        
        # === NUEVO: ENVIAR EL CORREO ===
        correo_enviado = enviar_correo_credenciales(correo, nombre, nuevo_usuario, nueva_password)
        
        if correo_enviado:
            flash(f'✅ Usuario {nuevo_usuario} creado. Las credenciales se han enviado a {correo}.')
        else:
            flash(f'⚠️ Usuario {nuevo_usuario} creado, pero hubo un error al enviar el correo. Contraseña generada: {nueva_password}')

    except psycopg2.IntegrityError:
        flash('❌ Error: El usuario o correo ya existe en el sistema.')
    except Exception as e:
        flash(f'❌ Error de base de datos: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

@app.route('/editar_usuario/<int:id>', methods=['POST'])
def editar_usuario(id):
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    nombre = request.form['nombre']
    rol = request.form['rol']
    estudios = request.form['estudios']
    correo = request.form['correo']

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE USUARIOS 
            SET nombre = %s, rol = %s, estudios = %s, correo = %s 
            WHERE id = %s
        ''', (nombre, rol, estudios, correo, id))
        conn.commit()
        cursor.close()
        
        registrar_accion(session['nombre'], f'Actualizó perfil del usuario ID {id}')
        flash('✅ Usuario actualizado correctamente.')
    except Exception as e:
        flash(f'❌ Error al actualizar el usuario: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    if id == session['id']:
        flash('❌ Operación denegada: No puedes eliminar tu propia cuenta mientras estás en sesión.')
        return redirect(url_for('admin'))

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM USUARIOS WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        
        registrar_accion(session['nombre'], f'Eliminó al usuario ID {id}')
        flash('🗑️ Usuario eliminado del sistema.')
    except Exception as e:
        flash(f'❌ Error al eliminar el usuario: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

@app.route('/restaurar_password/<int:id>', methods=['POST'])
def restaurar_password(id):
    # Validar seguridad
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    # Generar nueva contraseña aleatoria de 6 caracteres
    nueva_password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Primero obtenemos los datos del usuario para el correo
        cursor.execute('SELECT usuario, nombre, correo FROM USUARIOS WHERE id = %s', (id,))
        user_data = cursor.fetchone()

        if user_data:
            usuario_bd = user_data[0]
            nombre_bd = user_data[1]
            correo_bd = user_data[2]

            # Actualizamos la contraseña en la base de datos
            cursor.execute('UPDATE USUARIOS SET password = %s WHERE id = %s', (nueva_password, id))
            conn.commit()

            # Intentamos enviar el correo si el usuario tiene uno registrado
            if correo_bd:
                correo_enviado = enviar_correo_credenciales(correo_bd, nombre_bd, usuario_bd, nueva_password)
                if correo_enviado:
                    flash(f'🔑 Contraseña restaurada con éxito. Se ha enviado un correo a {correo_bd}.')
                else:
                    flash(f'⚠️ Contraseña restaurada, pero falló el envío del correo. NUEVA CONTRASEÑA: {nueva_password}')
            else:
                flash(f'⚠️ Contraseña restaurada. El usuario no tiene correo. NUEVA CONTRASEÑA: {nueva_password}')

        cursor.close()
    except Exception as e:
        flash(f'❌ Error al restaurar la contraseña: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

# ==========================================
# DASHBOARD DEL INVESTIGADOR
# ==========================================

@app.route('/dashboard')
def dashboard():
    # Validar que sea un investigador
    if 'usuario' in session and session['rol'] == 'investigador':
        conn = None
        try:
            conn = obtener_conexion()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # 1. Obtener la lectura más reciente
            cursor.execute('SELECT * FROM HISTORIAL_SENSORES ORDER BY fecha_hora DESC LIMIT 1')
            ultima_lectura = cursor.fetchone()

            # 2. Obtener las últimas 10 lecturas para la tabla del historial
            cursor.execute('SELECT * FROM HISTORIAL_SENSORES ORDER BY fecha_hora DESC LIMIT 10')
            historial = cursor.fetchall()

            # 3. Lotes activos (para el carrusel)
            cursor.execute("SELECT * FROM LOTES WHERE estado = 'activo' ORDER BY numero ASC")
            lotes = cursor.fetchall()

            cursor.close()

            # 4. LÓGICA DE ALERTAS 🚨
            alerta = None
            if ultima_lectura:
                # Extraemos los valores. Usamos float() por si la BD los devuelve como Decimal
                temp = float(ultima_lectura['temperatura']) if ultima_lectura['temperatura'] else 0
                hum = float(ultima_lectura['humedad']) if ultima_lectura['humedad'] else 0

                # Definir rangos críticos (Ejemplo: Pollo = 37.5°C a 38.0°C)
                if temp < 36.5 or temp > 38.5:
                    alerta = f"¡ALERTA CRÍTICA! Temperatura fuera de rango: {temp}°C. Revise el sistema de calentamiento."
                elif hum < 50 or hum > 70:
                    alerta = f"¡ADVERTENCIA! Humedad anormal detectada: {hum}%. Verifique el nivel de agua."

            return render_template('dashboard-investigador.html', 
                                   nombre_usuario=session['nombre'],
                                   sensores=ultima_lectura,
                                   historial=historial,
                                   lotes=lotes,
                                   alerta=alerta)

        except Exception as e:
            flash(f'Error al cargar los datos de los sensores: {e}')
            return render_template('dashboard-investigador.html', nombre_usuario=session['nombre'], historial=[], lotes=[])
        finally:
            if conn is not None:
                conn.close()

    flash('Debes iniciar sesión como investigador para ver esta página.')
    return redirect(url_for('index'))

# ==========================================
# API ENDPOINTS (JSON) PARA GRÁFICAS
# ==========================================

@app.route('/api/sensores')
def api_sensores():
    """Retorna la última lectura de sensores en formato JSON."""
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM HISTORIAL_SENSORES ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        cursor.close()

        if row:
            return jsonify({
                'temperatura': float(row['temperatura']) if row['temperatura'] else 0,
                'humedad': float(row['humedad']) if row['humedad'] else 0,
                'distancia': float(row['distancia']) if row['distancia'] else 0,
                'fecha_hora': row['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S') if row['fecha_hora'] else ''
            })
        return jsonify({'temperatura': 0, 'humedad': 0, 'distancia': 0, 'fecha_hora': ''})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route('/api/historial')
def api_historial():
    """
    Retorna el historial de lecturas de sensores.
    Parámetro: ?rango=dia|semana|mes (default: dia)
    """
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    rango = request.args.get('rango', 'dia')

    # Mapear el rango a un intervalo SQL
    intervalos = {
        'dia': "INTERVAL '1 day'",
        'semana': "INTERVAL '7 days'",
        'mes': "INTERVAL '30 days'"
    }
    intervalo = intervalos.get(rango, "INTERVAL '1 day'")

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f'''
            SELECT temperatura, humedad, distancia, fecha_hora 
            FROM HISTORIAL_SENSORES 
            WHERE fecha_hora >= NOW() - {intervalo}
            ORDER BY fecha_hora ASC
        ''')
        rows = cursor.fetchall()
        cursor.close()

        datos = []
        for row in rows:
            datos.append({
                'temperatura': float(row['temperatura']) if row['temperatura'] else 0,
                'humedad': float(row['humedad']) if row['humedad'] else 0,
                'distancia': float(row['distancia']) if row['distancia'] else 0,
                'fecha_hora': row['fecha_hora'].strftime('%Y-%m-%d %H:%M') if row['fecha_hora'] else ''
            })

        return jsonify(datos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route('/api/actuadores', methods=['GET', 'POST'])
def api_actuadores():
    """Maneja el estado actual de los actuadores (calefactor, ventilador, rotacion)"""
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if request.method == 'GET':
            cursor.execute('SELECT calefactor, ventilador, rotacion FROM ESTADO_ACTUADORES ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return jsonify({
                    'calefactor': bool(row['calefactor']),
                    'ventilador': bool(row['ventilador']),
                    'rotacion': float(row['rotacion']) if row['rotacion'] else 0.0
                })
            return jsonify({'calefactor': False, 'ventilador': False, 'rotacion': 45.0})
            
        elif request.method == 'POST':
            # Actualiza el valor de un actuador
            data = request.json
            if not data:
                return jsonify({'error': 'No JSON payload'}), 400
                
            actuador = data.get('actuador')
            valor = data.get('valor')
            lote_id = data.get('lote_id')
            
            if actuador in ['calefactor', 'ventilador']:
                cursor.execute(f'UPDATE ESTADO_ACTUADORES SET {actuador} = %s', (bool(valor),))
                estado_str = 'ENCENDIÓ' if valor else 'APAGÓ'
                registrar_accion(session['nombre'], f'{estado_str} forzosamente el {actuador.capitalize()}')
            elif actuador == 'rotacion':
                cursor.execute('UPDATE ESTADO_ACTUADORES SET rotacion = %s', (float(valor),))
                registrar_accion(session['nombre'], f'Ajustó la Rotación manual a {valor}°')
                
                if lote_id:
                    cursor.execute('UPDATE LOTES SET ultimo_volteo = CURRENT_TIMESTAMP WHERE id = %s', (int(lote_id),))
                    
            else:
                return jsonify({'error': 'Actuador desconocido'}), 400
                
            conn.commit()
            cursor.close()
            return jsonify({'success': True, 'actuador': actuador, 'valor': valor})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

# ==========================================
# GESTIÓN DE LOTES
# ==========================================

@app.route('/agregar_lote', methods=['POST'])
def agregar_lote():
    if 'usuario' not in session:
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    conn = None
    siguiente_numero = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Obtener el siguiente número de lote
        cursor.execute('SELECT COALESCE(MAX(numero), 0) + 1 FROM LOTES')
        siguiente_numero = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO LOTES (numero) VALUES (%s)
        ''', (siguiente_numero,))

        conn.commit()
        cursor.close()
        
        registrar_accion(session['nombre'], f'Creó un nuevo Lote (#{str(siguiente_numero).zfill(2)})')
        flash(f'✅ Lote #{str(siguiente_numero).zfill(2)} creado exitosamente.')
    except Exception as e:
        flash(f'❌ Error al crear lote: {e}')
    finally:
        if conn is not None:
            conn.close()

    # Redirigir según el rol
    if session.get('rol') == 'admin':
        return redirect(url_for('admin'))
    return redirect(url_for('dashboard'))

@app.route('/eliminar_lote/<int:id>', methods=['POST'])
def eliminar_lote(id):
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM LOTES WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        
        registrar_accion(session['nombre'], f'Eliminó el Lote ID ({id})')
        flash('🗑️ Lote eliminado del sistema.')
    except Exception as e:
        flash(f'❌ Error al eliminar lote: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

@app.route('/marcar_lote/<int:id>', methods=['POST'])
def marcar_lote(id):
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    estado = request.form.get('estado', 'empollado')

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('UPDATE LOTES SET estado = %s WHERE id = %s', (estado, id))
        conn.commit()
        cursor.close()
        
        registrar_accion(session['nombre'], f'Marcó Lote ID ({id}) como {estado}')
        flash(f'✅ Lote marcado como {estado}.')
    except Exception as e:
        flash(f'❌ Error al actualizar lote: {e}')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('admin'))

@app.route('/api/lotes')
def api_lotes():
    """Retorna los lotes activos en formato JSON."""
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM LOTES WHERE estado = 'activo' ORDER BY numero ASC")
        rows = cursor.fetchall()
        cursor.close()

        lotes = []
        ahora = datetime.now()
        for row in rows:
            fecha_creacion = row['fecha_creacion']
            if fecha_creacion.tzinfo:
                ahora_tz = datetime.now(timezone.utc)
                dias_transcurridos = (ahora_tz - fecha_creacion).days
            else:
                dias_transcurridos = (ahora - fecha_creacion).days

            lotes.append({
                'id': row['id'],
                'numero': row['numero'],
                'fecha_creacion': fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                'dias_transcurridos': dias_transcurridos,
                'dias_incubacion': row['dias_incubacion'],
                'estado': row['estado'],
                'ultimo_volteo': row['ultimo_volteo'].strftime('%Y-%m-%d %H:%M:%S') if row.get('ultimo_volteo') else None
            })

        return jsonify(lotes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

# ==========================================
# EJECUCIÓN DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
