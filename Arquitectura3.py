import sqlite3
import subprocess
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.client as mqtt


# Función para obtener la información del sistema
def obtener_informacion():
    comando_memoria = "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value"
    resultado_memoria = subprocess.run(comando_memoria, shell=True, capture_output=True, text=True)
    memoria_info = resultado_memoria.stdout.strip().splitlines()

    memoria_total = 0
    memoria_disponible = 0

    for line in memoria_info:
        if "TotalVisibleMemorySize" in line:
            memoria_total = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB
        elif "FreePhysicalMemory" in line:
            memoria_disponible = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB

    memoria_usada = memoria_total - memoria_disponible
    porcentaje_uso_memoria = (memoria_usada / memoria_total) * 100 if memoria_total > 0 else 0

    comando_rendimiento_red = "wmic NIC get BytesSentPersec /Value"
    resultado_rendimiento_red = subprocess.run(comando_rendimiento_red, shell=True, capture_output=True, text=True)

    lineas = resultado_rendimiento_red.stdout.strip().splitlines()
    rendimiento_red = 0

    for line in lineas:
        if "BytesSentPersec" in line:
            rendimiento_red = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB
            break

    comando_temperatura_cpu = "wmic /namespace:\\\\root\\cimv2 PATH Win32_PerfFormattedData_Counters_ThermalZoneInformation get Temperature /Value"
    resultado_temperatura_cpu = subprocess.run(comando_temperatura_cpu, shell=True, capture_output=True, text=True)

    lineas_temperatura = resultado_temperatura_cpu.stdout.splitlines()
    temperatura_cpu = "No disponible en esta plataforma"

    for linea in lineas_temperatura:
        if "Temperature" in linea:
            temperatura_cpu = linea.split('=')[1].strip()
            break

    # Crear mensaje con la información recolectada
    mensaje = (
        f"Memoria disponible: {memoria_disponible} MB\n"
        f"Porcentaje de uso de la memoria: {porcentaje_uso_memoria:.2f}%\n"
        f"Rendimiento de la red: {rendimiento_red:.2f} MB\n"
        f"Temperatura del CPU: {temperatura_cpu}"
    )
    guardar_en_base_de_datos(mensaje)
    print("Guardando en la base de datos:", mensaje)

    return mensaje
# Función para guardar datos en la base de datos SQLite
def guardar_en_base_de_datos(mensaje):
    conexion = sqlite3.connect('informacion_sistema.db')
    cursor = conexion.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datos_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            informacion TEXT
        )
    ''')

    # Insertar la información en la base de datos
    cursor.execute('INSERT INTO datos_sistema (informacion) VALUES (?)', (mensaje,))
    conexion.commit()
    conexion.close()



# Función para enviar correo electrónico
def enviar_email(subject, body):
    # Configurar los detalles del correo electrónico
    remitente_email = 'mijalchamorro27@gmail.com'  # Coloca tu dirección de Gmail
    destinatario_email = 'vasalinas21@gmail.com'  # Coloca la dirección del destinatario
    password = 'asct jxkh ftce oqax'  # Coloca la contraseña de tu cuenta de Gmail

    # Configurar el servidor SMTP de Gmail
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Crear el mensaje de correo
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente_email
    mensaje['To'] = destinatario_email
    mensaje['Subject'] = subject
    mensaje.attach(MIMEText(body, 'plain'))

    # Iniciar sesión en el servidor SMTP de Gmail
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(remitente_email, password)

    # Enviar el correo electrónico
    server.sendmail(remitente_email, destinatario_email, mensaje.as_string())

    # Cerrar la conexión con el servidor SMTP
    server.quit()

# Configuración de MQTT
broker_address = "mqtt-dashboard.com"  # Reemplaza con la dirección del broker MQTT
port = 8884  # Reemplaza con el puerto adecuado para WebSockets
topic = "Prueba"  # Define el tema al que enviarás la información

# Crear instancia del cliente MQTT
client = mqtt.Client(transport="websockets")

# Función de conexión a MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado con resultado code " + str(rc))
    client.subscribe(topic)  # Suscribirse al tema donde recibirá la información

# Función para manejar los mensajes recibidos
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))  # Imprimir los mensajes recibidos
    guardar_en_base_de_datos(str(msg.payload))
    print("Guardando en la base de datos:", str(msg.payload))

# Asignar las funciones de conexión y manejo de mensajes
client.on_connect = on_connect
client.on_message = on_message

# Habilitar el cifrado TLS
client.tls_set()

# Conectar al broker MQTT
client.connect(broker_address, port, 60)
# Suscribirse al tema para recibir información
client.subscribe(topic)
# Bucle para mantener la conexión y recibir información
client.loop_start()

# Bucle para enviar información cada 10 segundos
while True:
    # Obtener información del sistema
    mensaje = obtener_informacion()

    # Obtener el porcentaje de uso de la memoria de la información obtenida
    porcentaje_uso_memoria = float(mensaje.split('\n')[1].split(': ')[1][:-3])

    # Publicar mensaje en el topic definido
    client.publish(topic, mensaje)
    # Verificar si el porcentaje de uso de la memoria es mayor al 40%
    if porcentaje_uso_memoria > 40:
        # Enviar correo electrónico si se supera el límite
        subject = 'Uso alto de memoria'
        body = f"El porcentaje de uso de la memoria es: {porcentaje_uso_memoria:.2f}%"
        enviar_email(subject, body)

    # Esperar 10 segundos antes de enviar la próxima actualización
    time.sleep(10)

# Mantener la conexión MQTT
client.loop_forever()
# Diferencia de metadata- obtener info de equipos
def obtener_info_equipo(ip_equipo):
    comando_memoria = "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value"
    resultado_memoria = subprocess.run(comando_memoria, shell=True, capture_output=True, text=True)
    memoria_info = resultado_memoria.stdout.strip().splitlines()

    memoria_total = 0
    memoria_disponible = 0

    for line in memoria_info:
        if "TotalVisibleMemorySize" in line:
            memoria_total = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB
        elif "FreePhysicalMemory" in line:
            memoria_disponible = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB

    memoria_usada = memoria_total - memoria_disponible
    porcentaje_uso_memoria = (memoria_usada / memoria_total) * 100 if memoria_total > 0 else 0

    comando_rendimiento_red = "wmic NIC get BytesSentPersec /Value"
    resultado_rendimiento_red = subprocess.run(comando_rendimiento_red, shell=True, capture_output=True, text=True)

    lineas = resultado_rendimiento_red.stdout.strip().splitlines()
    rendimiento_red = 0

    for line in lineas:
        if "BytesSentPersec" in line:
            rendimiento_red = int(line.split('=')[1]) // (1024**2)  # Convertir bytes a MB
            break

    comando_temperatura_cpu = "wmic /namespace:\\\\root\\cimv2 PATH Win32_PerfFormattedData_Counters_ThermalZoneInformation get Temperature /Value"
    resultado_temperatura_cpu = subprocess.run(comando_temperatura_cpu, shell=True, capture_output=True, text=True)

    lineas_temperatura = resultado_temperatura_cpu.stdout.splitlines()
    temperatura_cpu = "No disponible en esta plataforma"

    for linea in lineas_temperatura:
        if "Temperature" in linea:
            temperatura_cpu = linea.split('=')[1].strip()
            break

    # Crear mensaje con la información recolectada
    informacion_equipo = (
        f"Memoria disponible: {memoria_disponible} MB\n"
        f"Porcentaje de uso de la memoria: {porcentaje_uso_memoria:.2f}%\n"
        f"Rendimiento de la red: {rendimiento_red:.2f} MB\n"
        f"Temperatura del CPU: {temperatura_cpu}"
    )
    return informacion_equipo


