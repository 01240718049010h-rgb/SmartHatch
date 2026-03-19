"""
Servidor MQTT - SmartHatch IoT
==============================
Script independiente que actúa como puente entre el ESP32 y la base de datos.
Se suscribe al broker MQTT, recibe los datos de sensores en formato JSON
y los guarda en la tabla HISTORIAL_SENSORES de PostgreSQL (Render).

Ejecución: python Servidor.py
"""

import paho.mqtt.client as mqtt
import psycopg2
import json
import time

# ==========================================
# CONFIGURACIÓN
# ==========================================

# Base de datos PostgreSQL en Render
DATABASE_URL = "postgresql://smarthatch_db_user:8zdKUU03sgVXqKfInHKKIkjIxyLqs1sx@dpg-d6t0phfgi27c73dctv6g-a.virginia-postgres.render.com/smarthatch_db"

# Configuración del Broker MQTT
MQTT_BROKER = "mqtt-dashboard.com"   # Broker público gratuito (cambiar si usas otro)
MQTT_PORT = 1883
MQTT_TOPIC = "incubadora/sensores"  # Topic donde el ESP32 publica los datos
MQTT_CLIENT_ID = "SmartHatch_Server"

# ==========================================
# FUNCIONES MQTT
# ==========================================

def on_connect(client, userdata, flags, rc):
    """Se ejecuta al conectarse al broker MQTT."""
    if rc == 0:
        print("=" * 50)
        print("✅ Conectado al broker MQTT exitosamente")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Topic:  {MQTT_TOPIC}")
        print("=" * 50)
        print("👂 Escuchando datos de la incubadora...\n")
        # Suscribirse al topic del ESP32
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Error de conexión al broker MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    """Se ejecuta cada vez que llega un mensaje del ESP32."""
    payload = msg.payload.decode('utf-8')
    print(f"📩 Mensaje recibido en [{msg.topic}]: {payload}")

    try:
        # Decodificar el JSON del ESP32
        # Formato esperado: {"temp": 37.5, "hum": 60.2, "dist": 15.0}
        datos = json.loads(payload)
        temperatura = datos.get('temp', 0)
        humedad = datos.get('hum', 0)
        distancia = datos.get('dist', 0)

        print(f"   🌡️ Temp: {temperatura}°C | 💧 Hum: {humedad}% | 📏 Dist: {distancia}cm")

        # Guardar en PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SET timezone = 'America/Merida';")

        cursor.execute('''
            INSERT INTO HISTORIAL_SENSORES (temperatura, humedad, distancia)
            VALUES (%s, %s, %s)
        ''', (temperatura, humedad, distancia))

        conn.commit()
        cursor.close()
        conn.close()
        print("   ✅ Registro guardado en la nube con éxito\n")

    except json.JSONDecodeError:
        print("   ❌ Error: El mensaje no es un JSON válido.\n")
    except Exception as e:
        print(f"   ❌ Error al guardar en base de datos: {e}\n")


def on_disconnect(client, userdata, rc):
    """Se ejecuta cuando se pierde la conexión con el broker."""
    print("⚠️ Desconectado del broker MQTT. Intentando reconectar...")


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == '__main__':
    print("\n🐣 SmartHatch - Servidor MQTT IoT")
    print("Conectando al broker MQTT...\n")

    # Crear cliente MQTT
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)

    # Asignar funciones callback
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        # Conectar al broker
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

        # Bucle infinito: escuchar mensajes 24/7
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario.")
        client.disconnect()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        print("Verifica tu conexión a internet y las credenciales del broker.")
