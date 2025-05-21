import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import psutil  # Librería para obtener información del sistema y procesos
import platform  # Para obtener información sobre la plataforma/OS
import cpuinfo  # Librería para obtener información detallada del CPU
import GPUtil  # Librería para obtener información de GPU
import socket  # Para información de red
import shutil  # Para obtener información de disco
import datetime  # Para manejar fechas y tiempos
import matplotlib.pyplot as plt  # Para crear gráficas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Para integrar matplotlib con tkinter
from matplotlib.backends.backend_pdf import PdfPages  # Para crear PDFs con matplotlib
import numpy as np  # Para cálculos numéricos
import pandas as pd  # Para manejo de datos estructurados
from PIL import Image, ImageTk  # Para manejo de imágenes
import threading  # Para paralelizar tareas y no bloquear la interfaz
import sv_ttk  # Tema Sun Valley para Tkinter (estilo moderno)
import matplotlib  # Base de matplotlib
import os  # Operaciones del sistema de archivos
import sys  # Acceso a variables y funciones específicas del sistema
import time  # Para medir tiempos
import re  # Para expresiones regulares (búsqueda avanzada)
from concurrent.futures import ThreadPoolExecutor  # Para ejecutar tareas en paralelo
import queue  # Para comunicación entre hilos
import io  # Para manejo de streams de entrada/salida
from reportlab.lib.pagesizes import A4  # Para configurar tamaño de página en reportes PDF
from reportlab.lib import colors  # Para manejar colores en reportes PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage  # Componentes para crear PDFs
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # Estilos para PDFs
from reportlab.lib.units import inch, cm  # Unidades de medida para PDFs


def recurso_ruta(rel_path):
    """Devuelve la ruta absoluta al recurso, sea compilado o no
    
    Esta función maneja tanto la ejecución normal como cuando
    la aplicación está compilada con PyInstaller, donde los recursos
    están en un sistema de archivos virtual (_MEIPASS)"""
    try:
        base_path = sys._MEIPASS  # Path base cuando se ejecuta con PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # Path base en ejecución normal
    return os.path.join(base_path, rel_path)

# Configurar matplotlib cache
# Esto evita problemas de permisos al crear el directorio de caché de matplotlib
if hasattr(sys, "_MEIPASS"):
    cache_path = recurso_ruta("matplotlib_cache")
    os.environ["MPLCONFIGDIR"] = cache_path
else:
    os.environ["MPLCONFIGDIR"] = os.path.abspath("./matplotlib_cache")

# Cache global para procesos
# Implementa un sistema de caché para evitar consultar los procesos constantemente
proceso_cache = {
    'data': [],  # Almacena los datos de procesos
    'last_update': 0,  # Timestamp de la última actualización
    'cache_duration': 2.0  # Duración de la caché en segundos
}

# Cola para comunicación entre hilos
# Permite comunicar actualizaciones entre el hilo principal y los hilos de procesamiento
update_queue = queue.Queue()

# --- CONFIGURACION GRAFICA ---
# Almacena configuración de colores y estilos para las gráficas
grafico_config = {
    "cpu_color": "#00ff00",  # Verde para CPU
    "ram_color": "#ff6600",  # Naranja para RAM
    "disco_color": "#0099ff",  # Azul para Disco
    "red_color": "#ff0066",  # Rosa para Red
    "estilo": "line"  # Estilo predeterminado: línea (alternativa: barras)
}

# Almacena referencias a las funciones de actualización de cada gráfica
graficas_act = {}

# --- SISTEMA DE TRADUCCIÓN ---
# Diccionario con todas las cadenas de texto traducidas
IDIOMAS = {
    "es": {
        # Interfaz general
        "titulo_app": "Leo-G",
        "actualizar": "Actualizar información",
        "obteniendo_info": "Obteniendo información del sistema...",
        
        # Pestañas
        "tab_sistema": "Sistema",
        "tab_procesos": "Procesos",
        "tab_graficas": "Gráficas",
        "tab_config": "Configuración",
        "tab_grabacion": "Grabación",
        
        # Información del sistema
        "sistema_operativo": "Sistema operativo",
        "nombre_equipo": "Nombre del equipo",
        "arquitectura": "Arquitectura",
        "procesador": "Procesador",
        "ram_total": "RAM total",
        "disco_total": "Disco total",
        "gpu": "GPU",
        "uptime": "Uptime",
        "red": "Red",
        "interfaces_red": "Interfaces de red:",
        
        # Procesos
        "busqueda_avanzada": "Búsqueda avanzada",
        "ejemplos_busqueda": "💡 Ejemplos: 'chrome', 'cpu>50', 'ram<10', PID numérico",
        "cpu_alto": "CPU Alto (>50%)",
        "ram_alto": "RAM Alto (>50%)",
        "limpiar": "Limpiar",
        "mostrando": "Mostrando",
        "de": "de",
        "procesos": "procesos",
        
        # Columnas procesos
        "pid": "PID",
        "nombre": "Nombre",
        "cpu_percent": "CPU %",
        "ram_percent": "RAM %",
        "hilos": "Hilos",
        
        # Menú contextual
        "terminar_proceso": "Terminar proceso",
        "copiar_pid": "Copiar PID",
        "info_detallada": "Información detallada",
        "confirmar": "Confirmar",
        "pregunta_terminar": "¿Terminar proceso {0} (PID: {1})?",
        "exito": "Éxito",
        "proceso_terminado": "Proceso {0} terminado",
        "error": "Error",
        "error_terminar": "No se pudo terminar el proceso: {0}",
        "copiado": "Copiado",
        "pid_copiado": "PID {0} copiado al portapapeles",
        "info_proceso_titulo": "Información del proceso",
        "info_proceso_detalle": """Información del proceso:
            
PID: {0}
Nombre: {1}
Estado: {2}
CPU: {3}%
Memoria: {4}%
Hilos: {5}
Creado: {6}
Usuario: {7}
""",
        
        # Gráficas
        "cpu": "CPU",
        "ram": "RAM",
        "disco": "Disco",
        "red": "Red",
        "red_mbs": "Red (MB/s)",
        "actual": "Actual",
        
        # Configuración
        "config_graficas": "Configuración de gráficas",
        "estilo_grafica": "Estilo de gráfica:",
        "linea": "Línea",
        "barras": "Barras",
        "colores_graficas": "Colores de gráficas",
        "color_para": "Color {0}",
        "config_rendimiento": "Configuración de rendimiento",
        "intervalo_act": "Intervalo de actualización (segundos):",
        "segundos": "segundos",
        "aplicar_config": "Aplicar configuración",
        "restaurar_pred": "Restaurar predeterminados",
        "exportar_config": "Exportar configuración",
        "config_idioma": "Configuración de idioma",
        "seleccionar_idioma": "Seleccionar idioma:",
        "aplicar_idioma": "Aplicar idioma",
        "idioma_aplicado": "Idioma aplicado correctamente",
        "reinicio_necesario": "Algunos cambios se aplicarán completamente al reiniciar la aplicación",
        "config_restaurada": "Configuración restaurada a valores predeterminados",
        "guardar_config": "Guardar configuración",
        "config_guardada": "Configuración guardada en {0}",
        "error_guardar": "No se pudo guardar la configuración: {0}",
        
        # Splash screen
        "cargando": "Cargando...",
        "monitor_sistema": "Monitor del Sistema",
        "iniciando": "Iniciando aplicación...",
        "cargando_info": "Cargando información del sistema...",
        "cargando_procesos": "Cargando procesos...",
        "config_graficas_splash": "Configurando gráficas...",
        "listo": "¡Listo!",
        "app_cerrada": "Aplicación cerrada por el usuario",
        "error_fatal": "Error fatal: {0}",
        
        # Pestaña de grabación
        "control_grabacion": "Control de grabación",
        "iniciar_grabacion": "Iniciar grabación",
        "detener_grabacion": "Detener grabación",
        "intervalo_grabacion": "Intervalo de grabación:",
        "estado_grabacion": "Estado de la grabación",
        "estado": "Estado",
        "hora_inicio": "Hora de inicio",
        "duracion": "Duración",
        "num_muestras": "Número de muestras",
        "grabando": "Grabando",
        "detenido": "Detenido",
        "valores_actuales": "Valores actuales",
        "generar_informe": "Generación de informe",
        "generar_pdf": "Generar PDF",
        "ayuda_informe": "El informe incluirá estadísticas y gráficos de rendimiento del periodo grabado",
        "procesando": "Procesando",
        "generando_pdf": "Generando informe PDF...",
        "no_datos_informe": "No hay datos suficientes para generar un informe",
        "error_generar_pdf": "Error al generar el PDF",
        "guardar_informe": "Guardar informe de rendimiento",
        "error_abrir_pdf": "Error al abrir el PDF",
        "abrir_pdf_pregunta": "¿Desea abrir el informe ahora?",
        "advertencia": "Advertencia"
    },
    "en": {
        # Traducción al inglés de todas las cadenas
        # General interface
        "titulo_app": "LeoG",
        "actualizar": "Update information",
        "obteniendo_info": "Getting system information...",
        
        # Tabs
        "tab_sistema": "System",
        "tab_procesos": "Processes",
        "tab_graficas": "Charts",
        "tab_config": "Settings",
        "tab_grabacion": "Recording",
        
        # System information
        "sistema_operativo": "Operating system",
        "nombre_equipo": "Computer name",
        "arquitectura": "Architecture",
        "procesador": "Processor",
        "ram_total": "Total RAM",
        "disco_total": "Total disk",
        "gpu": "GPU",
        "uptime": "Uptime",
        "red": "Network",
        "interfaces_red": "Network interfaces:",
        
        # Processes
        "busqueda_avanzada": "Advanced search",
        "ejemplos_busqueda": "💡 Examples: 'chrome', 'cpu>50', 'ram<10', numeric PID",
        "cpu_alto": "High CPU (>50%)",
        "ram_alto": "High RAM (>50%)",
        "limpiar": "Clear",
        "mostrando": "Showing",
        "de": "of",
        "procesos": "processes",
        
        # Processes columns
        "pid": "PID",
        "nombre": "Name",
        "cpu_percent": "CPU %",
        "ram_percent": "RAM %",
        "hilos": "Threads",
        
        # Context menu
        "terminar_proceso": "End process",
        "copiar_pid": "Copy PID",
        "info_detallada": "Detailed information",
        "confirmar": "Confirm",
        "pregunta_terminar": "End process {0} (PID: {1})?",
        "exito": "Success",
        "proceso_terminado": "Process {0} terminated",
        "error": "Error",
        "error_terminar": "Could not end process: {0}",
        "copiado": "Copied",
        "pid_copiado": "PID {0} copied to clipboard",
        "info_proceso_titulo": "Process information",
        "info_proceso_detalle": """Process information:
            
PID: {0}
Name: {1}
Status: {2}
CPU: {3}%
Memory: {4}%
Threads: {5}
Created: {6}
User: {7}
""",
        
        # Charts
        "cpu": "CPU",
        "ram": "RAM",
        "disco": "Disk",
        "red": "Network",
        "red_mbs": "Network (MB/s)",
        "actual": "Current",
        
        # Settings
        "config_graficas": "Chart settings",
        "estilo_grafica": "Chart style:",
        "linea": "Line",
        "barras": "Bar",
        "colores_graficas": "Chart colors",
        "color_para": "Color for {0}",
        "config_rendimiento": "Performance settings",
        "intervalo_act": "Update interval (seconds):",
        "segundos": "seconds",
        "aplicar_config": "Apply settings",
        "restaurar_pred": "Restore defaults",
        "exportar_config": "Export settings",
        "config_idioma": "Language settings",
        "seleccionar_idioma": "Select language:",
        "aplicar_idioma": "Apply language",
        "idioma_aplicado": "Language applied successfully",
        "reinicio_necesario": "Some changes will be fully applied after restarting the application",
        "config_restaurada": "Settings restored to default values",
        "guardar_config": "Save settings",
        "config_guardada": "Settings saved to {0}",
        "error_guardar": "Could not save settings: {0}",
        
        # Splash screen
        "cargando": "Loading...",
        "monitor_sistema": "System Monitor",
        "iniciando": "Starting application...",
        "cargando_info": "Loading system information...",
        "cargando_procesos": "Loading processes...",
        "config_graficas_splash": "Configuring charts...",
        "listo": "Ready!",
        "app_cerrada": "Application closed by user",
        "error_fatal": "Fatal error: {0}",
        
        # Recording tab
        "control_grabacion": "Recording Control",
        "iniciar_grabacion": "Start Recording",
        "detener_grabacion": "Stop Recording",
        "intervalo_grabacion": "Recording interval:",
        "estado_grabacion": "Recording Status",
        "estado": "Status",
        "hora_inicio": "Start time",
        "duracion": "Duration",
        "num_muestras": "Number of samples",
        "grabando": "Recording",
        "detenido": "Stopped",
        "valores_actuales": "Current Values",
        "generar_informe": "Report Generation",
        "generar_pdf": "Generate PDF",
        "ayuda_informe": "The report will include statistics and performance charts for the recorded period",
        "procesando": "Processing",
        "generando_pdf": "Generating PDF report...",
        "no_datos_informe": "Not enough data to generate a report",
        "error_generar_pdf": "Error generating PDF",
        "guardar_informe": "Save performance report",
        "error_abrir_pdf": "Error opening PDF",
        "abrir_pdf_pregunta": "Do you want to open the report now?",
        "advertencia": "Warning"
    }
}

# Idioma predeterminado
idioma_actual = "es"

def _(clave, *args):
    """Función para traducir textos según el idioma actual
    
    Similar a gettext, busca la clave en el diccionario del idioma actual
    y permite formatear el texto con parámetros adicionales"""
    if clave in IDIOMAS[idioma_actual]:
        texto = IDIOMAS[idioma_actual][clave]
        if args:
            return texto.format(*args)
        return texto
    return clave  # Si no encuentra la clave, devuelve la clave misma

# ----- CLASE PARA LA GRABACIÓN DEL RENDIMIENTO -----
class RegistradorRendimiento:
    """Clase que maneja la grabación de datos de rendimiento del sistema
    
    Se encarga de registrar en segundo plano las métricas de CPU, RAM,
    disco y red, y permite generar informes PDF con estadísticas"""
    
    def __init__(self, intervalo=1.0):
        self.intervalo = intervalo  # Segundos entre cada registro
        self.grabando = False
        self.datos = {
            'timestamp': [],  # Momentos de cada medición
            'cpu': [],        # Porcentajes de CPU
            'ram': [],        # Porcentajes de RAM
            'disco': [],      # Porcentajes de Disco
            'red': []         # Velocidad de red en MB/s
        }
        self.hora_inicio = None
        self.hora_fin = None
        self.thread = None
        self.callbacks = []  # Para actualizar UI mientras graba
    
    def iniciar_grabacion(self):
        """Inicia la grabación de datos de rendimiento"""
        if self.grabando:
            return False
        
        # Reiniciar datos
        self.datos = {
            'timestamp': [],
            'cpu': [],
            'ram': [],
            'disco': [],
            'red': []
        }
        self.hora_inicio = datetime.datetime.now()
        self.grabando = True
        
        # Iniciar thread para no bloquear la UI
        self.thread = threading.Thread(target=self._loop_grabacion, daemon=True)
        self.thread.start()
        return True
    
    def detener_grabacion(self):
        """Detiene la grabación actual"""
        if not self.grabando:
            return False
        
        self.grabando = False
        self.hora_fin = datetime.datetime.now()
        
        # Esperar a que termine el thread
        if self.thread:
            self.thread.join(timeout=2.0)
        
        return True
    
    def _loop_grabacion(self):
        """Loop principal de grabación
        
        Se ejecuta en un hilo separado y recopila datos periódicamente"""
        last_net_io = psutil.net_io_counters()
        last_net_time = time.time()
        
        while self.grabando:
            try:
                # Obtener datos actuales
                timestamp = datetime.datetime.now()
                cpu_percent = psutil.cpu_percent()
                ram_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Calcular velocidad de red
                current_net_io = psutil.net_io_counters()
                current_time = time.time()
                time_diff = current_time - last_net_time
                
                bytes_diff = (current_net_io.bytes_sent + current_net_io.bytes_recv) - \
                           (last_net_io.bytes_sent + last_net_io.bytes_recv)
                
                speed_mbps = (bytes_diff / time_diff) / (1024 * 1024) if time_diff > 0 else 0
                
                # Guardar valores
                self.datos['timestamp'].append(timestamp)
                self.datos['cpu'].append(cpu_percent)
                self.datos['ram'].append(ram_percent)
                self.datos['disco'].append(disk_percent)
                self.datos['red'].append(speed_mbps)
                
                # Actualizar valores de red para la próxima iteración
                last_net_io = current_net_io
                last_net_time = current_time
                
                # Ejecutar callbacks para actualizar UI
                for callback in self.callbacks:
                    try:
                        callback(self.obtener_estado())
                    except Exception as e:
                        print(f"Error en callback: {e}")
                
                # Esperar para la siguiente medición
                time.sleep(self.intervalo)
            
            except Exception as e:
                print(f"Error en grabación: {e}")
                time.sleep(self.intervalo)  # Continuar incluso si hay error
    
    def registrar_callback(self, callback):
        """Registra una función callback para actualizar UI
        
        Permite notificar a la interfaz sobre nuevos datos"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def quitar_callback(self, callback):
        """Quita un callback registrado"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def obtener_estado(self):
        """Devuelve un resumen del estado actual de grabación
        
        Incluye información sobre si está grabando, tiempo, 
        duración y últimos valores registrados"""
        duracion = None
        if self.hora_inicio:
            fin = self.hora_fin if self.hora_fin else datetime.datetime.now()
            duracion = fin - self.hora_inicio
        
        return {
            'grabando': self.grabando,
            'hora_inicio': self.hora_inicio,
            'hora_fin': self.hora_fin,
            'duracion': duracion,
            'muestras': len(self.datos['timestamp']),
            'ultimos_valores': {
                'cpu': self.datos['cpu'][-1] if self.datos['cpu'] else None,
                'ram': self.datos['ram'][-1] if self.datos['ram'] else None,
                'disco': self.datos['disco'][-1] if self.datos['disco'] else None,
                'red': self.datos['red'][-1] if self.datos['red'] else None
            } if self.datos['timestamp'] else None
        }
    
    def obtener_estadisticas(self):
        """Calcula estadísticas de los datos recolectados
        
        Retorna mínimo, máximo, promedio, mediana y desviación estándar
        para cada métrica registrada"""
        if not self.datos['timestamp']:
            return None
        
        stats = {}
        for key in ['cpu', 'ram', 'disco', 'red']:
            if not self.datos[key]:
                continue
            
            valores = np.array(self.datos[key])
            stats[key] = {
                'min': np.min(valores),
                'max': np.max(valores),
                'promedio': np.mean(valores),
                'mediana': np.median(valores),
                'desv_std': np.std(valores)
            }
        
        return stats
    
    def generar_pdf(self, ruta_archivo, info_sistema=None):
        """Genera un informe PDF con los datos recolectados
        
        Crea un informe profesional con información del sistema,
        estadísticas y gráficas de todas las métricas registradas"""
        if not self.datos['timestamp'] or len(self.datos['timestamp']) < 2:
            return False, "No hay suficientes datos para generar un informe"
        
        try:
            # Crear directorio si no existe
            directorio = os.path.dirname(ruta_archivo)
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio)
            
            # Configurar documento
            doc = SimpleDocTemplate(
                ruta_archivo,
                pagesize=A4,
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            styles.add(ParagraphStyle(
                name='Titulo',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                alignment=1  # Centro
            ))
            
            styles.add(ParagraphStyle(
                name='Subtitulo',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=10,
                spaceAfter=8
            ))
            
            styles.add(ParagraphStyle(
                name='Parrafo',
                parent=styles['Normal'],
                fontSize=10,
                leading=12,
                spaceBefore=6
            ))
            
            # Añadir título del informe
            elements.append(Paragraph("Informe de Rendimiento del Sistema", styles['Titulo']))
            
            # Información general
            elements.append(Paragraph("Información General", styles['Subtitulo']))
            
            fecha_inicio = self.hora_inicio.strftime("%d/%m/%Y %H:%M:%S")
            fecha_fin = self.hora_fin.strftime("%d/%m/%Y %H:%M:%S") if self.hora_fin else "N/A"
            duracion = str(self.hora_fin - self.hora_inicio).split('.')[0] if self.hora_fin else "N/A"
            
            data = [
                ["Fecha de inicio", fecha_inicio],
                ["Fecha de finalización", fecha_fin],
                ["Duración", duracion],
                ["Número de muestras", str(len(self.datos['timestamp']))]
            ]
            
            # Añadir información del sistema si está disponible
            if info_sistema:
                for clave, valor in info_sistema.items():
                    if clave != "Red":  # La red se maneja diferente
                        data.append([clave, str(valor)])
                
                # Añadir interfaces de red
                if "Red" in info_sistema:
                    interfaces = []
                    for interfaz, ip in info_sistema["Red"].items():
                        interfaces.append(f"{interfaz}: {ip}")
                    data.append(["Interfaces de red", "\n".join(interfaces)])
            
            # Crear tabla
            tabla = Table(data, colWidths=[4*cm, 12*cm])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9)
            ]))
            elements.append(tabla)
            elements.append(Spacer(1, 0.5*cm))
            
            # Estadísticas
            elements.append(Paragraph("Estadísticas", styles['Subtitulo']))
            
            stats = self.obtener_estadisticas()
            
            if stats:
                header = ["Métrica", "Mínimo", "Máximo", "Promedio", "Mediana", "Desv. Estándar"]
                data = [header]
                
                for key, values in stats.items():
                    unidad = "MB/s" if key == "red" else "%"
                    row = [
                        key.upper(),
                        f"{values['min']:.2f} {unidad}",
                        f"{values['max']:.2f} {unidad}",
                        f"{values['promedio']:.2f} {unidad}",
                        f"{values['mediana']:.2f} {unidad}",
                        f"{values['desv_std']:.2f} {unidad}"
                    ]
                    data.append(row)
                
                tabla = Table(data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9)
                ]))
                elements.append(tabla)
                elements.append(Spacer(1, 0.5*cm))
            
            # Generar y guardar gráficos
            elementos_por_pagina = 2  # Gráficos por página
            metricas = ['cpu', 'ram', 'disco', 'red']
            titulos = {
                'cpu': 'CPU (%)',
                'ram': 'RAM (%)',
                'disco': 'Disco (%)',
                'red': 'Red (MB/s)'
            }
            colores = {
                'cpu': '#00ff00',
                'ram': '#ff6600',
                'disco': '#0099ff',
                'red': '#ff0066'
            }
            
            for i, metrica in enumerate(metricas):
                if i % elementos_por_pagina == 0 and i > 0:
                    elements.append(Spacer(1, 0.2*cm))  # Pequeño espacio entre gráficos
                
                # Título del gráfico
                elements.append(Paragraph(f"Gráfico de {titulos[metrica]}", styles['Subtitulo']))
                
                # Crear gráfico con matplotlib
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Convertir timestamps a formato de tiempo relativo en minutos
                tiempo_base = self.datos['timestamp'][0]
                tiempo_rel = [(t - tiempo_base).total_seconds() / 60 for t in self.datos['timestamp']]
                
                ax.plot(tiempo_rel, self.datos[metrica], color=colores[metrica], linewidth=2)
                ax.fill_between(tiempo_rel, self.datos[metrica], alpha=0.3, color=colores[metrica])
                
                ax.set_title(titulos[metrica])
                ax.set_xlabel('Tiempo (minutos)')
                ax.set_ylabel(titulos[metrica])
                ax.grid(True, alpha=0.3)
                
                # Guardar gráfico a un buffer y convertir a imagen para reportlab
                img_data = io.BytesIO()
                fig.savefig(img_data, format='png', bbox_inches='tight')
                img_data.seek(0)
                
                # Cerrar figura para liberar memoria
                plt.close(fig)
                
                # Crear imagen para el PDF
                img = RLImage(img_data, width=16*cm, height=8*cm)
                elements.append(img)
                elements.append(Spacer(1, 0.5*cm))
            
            # Construir PDF
            doc.build(elements)
            
            return True, "Informe generado correctamente"
            
        except Exception as e:
            return False, f"Error al generar el informe: {str(e)}"

# --- FUNCIONES OPTIMIZADAS ---
def obtener_info_sistema():
    """Obtiene información del sistema de forma optimizada
    
    Recopila datos sobre sistema operativo, CPU, memoria, disco,
    interfaces de red, etc., de manera eficiente"""
    try:
        uname = platform.uname()
        
        # Obtener CPU info de forma segura
        try:
            cpu = cpuinfo.get_cpu_info()['brand_raw']
        except:
            cpu = platform.processor() or "No detectado"
        
        memoria = psutil.virtual_memory()
        disco_total, _, _ = shutil.disk_usage("/")
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        
        # Optimizar obtención de interfaces de red
        red = {}
        try:
            interfaces = psutil.net_if_addrs()
            for interfaz, direcciones in interfaces.items():
                for dir in direcciones:
                    if dir.family == socket.AF_INET and dir.address != '127.0.0.1':
                        red[interfaz] = dir.address
                        break  # Solo tomar la primera IP válida
        except:
            red = {"No disponible": "Error"}
        
        # GPU info optimizada
        try:
            gpus = GPUtil.getGPUs()
            gpu_info = gpus[0].name if gpus else "No detectada"
        except:
            gpu_info = "No detectada"
        
        # Usar cadenas fijas para las claves para asegurar compatibilidad
        return {
            "Sistema operativo": f"{uname.system} {uname.release}",
            "Nombre del equipo": uname.node,
            "Arquitectura": f"{uname.machine} - {platform.architecture()[0]}",
            "Procesador": cpu,
            "RAM total": f"{round(memoria.total / (1024**3), 2)} GB",
            "Disco total": f"{round(disco_total / (1024**3), 2)} GB",
            "GPU": gpu_info,
            "Uptime": str(uptime).split('.')[0],
            "Red": red,
        }
    except Exception as e:
        return {"Error": f"No se pudo obtener información del sistema: {str(e)}"}

def obtener_procesos_optimizado():
    """Obtiene lista de procesos de forma optimizada con cache
    
    Aprovecha el sistema de caché para evitar consultas frecuentes
    que podrían degradar el rendimiento"""
    current_time = time.time()
    
    # Verificar cache
    if (current_time - proceso_cache['last_update']) < proceso_cache['cache_duration']:
        return proceso_cache['data']
    
    try:
        # Obtener procesos en paralelo
        procesos = []
        attrs = ['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']
        
        for p in psutil.process_iter(attrs=attrs):
            try:
                info = p.info
                if info['pid'] is not None and info['name']:
                    procesos.append((
                        info['pid'],
                        info['name'],
                        round(info['cpu_percent'] or 0, 1),
                        round(info['memory_percent'] or 0, 1),
                        info['num_threads'] or 0
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Actualizar cache
        proceso_cache['data'] = sorted(procesos, key=lambda x: x[2], reverse=True)
        proceso_cache['last_update'] = current_time
        
        return proceso_cache['data']
    except Exception as e:
        print(f"{_('error_procesos')}: {e}")
        return []

def buscar_procesos_avanzada(procesos, filtro):
    """Búsqueda avanzada de procesos con regex y múltiples criterios
    
    Permite buscar por nombre, PID o condiciones como 'cpu>50' o 'ram<10'"""
    if not filtro:
        return procesos
    
    filtro = filtro.lower().strip()
    resultados = []
    
    # Verificar si es un PID
    if filtro.isdigit():
        pid_filtro = int(filtro)
        for proc in procesos:
            if proc[0] == pid_filtro:
                resultados.append(proc)
        return resultados
    
    # Verificar si es un filtro de CPU/RAM (ej: "cpu>50", "ram<10")
    cpu_match = re.match(r'cpu([<>]=?)(\d+(?:\.\d+)?)', filtro)
    ram_match = re.match(r'ram([<>]=?)(\d+(?:\.\d+)?)', filtro)
    
    if cpu_match:
        op, valor = cpu_match.groups()
        valor = float(valor)
        for proc in procesos:
            if evaluar_condicion(proc[2], op, valor):
                resultados.append(proc)
        return resultados
    
    if ram_match:
        op, valor = ram_match.groups()
        valor = float(valor)
        for proc in procesos:
            if evaluar_condicion(proc[3], op, valor):
                resultados.append(proc)
        return resultados
    
    # Búsqueda por nombre (con soporte para regex básico)
    try:
        # Intentar como regex
        patron = re.compile(filtro, re.IGNORECASE)
        for proc in procesos:
            if patron.search(proc[1]):
                resultados.append(proc)
    except re.error:
        # Si falla regex, búsqueda normal
        for proc in procesos:
            if filtro in proc[1].lower():
                resultados.append(proc)
    
    return resultados

def evaluar_condicion(valor, operador, referencia):
    """Evalúa condiciones para filtros numéricos
    
    Implementa operadores de comparación para la búsqueda avanzada"""
    if operador == '>':
        return valor > referencia
    elif operador == '<':
        return valor < referencia
    elif operador == '>=':
        return valor >= referencia
    elif operador == '<=':
        return valor <= referencia
    return False

# ----- CLASE PARA LA PESTAÑA DE GRABACIÓN -----
class TabGrabacion:
    """Clase que implementa la pestaña de grabación de rendimiento
    
    Permite iniciar/detener grabaciones y generar informes PDF
    con los datos recopilados"""
    
    def __init__(self, notebook, app, iconos=None):
        self.notebook = notebook
        self.app = app
        self.iconos = iconos or {}
        self.registrador = RegistradorRendimiento()
        
        # Crear pestaña
        self.tab_grabacion = ttk.Frame(notebook)
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("grabacion"):
            self.notebook.add(self.tab_grabacion, text=f" {_('tab_grabacion')}", 
                             image=self.iconos.get("grabacion"), compound="left")
        else:
            self.notebook.add(self.tab_grabacion, text=f" {_('tab_grabacion')}")
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Iniciar actualizaciones periódicas del estado
        self.actualizar_estado()
    
    def crear_interfaz(self):
        """Crea la interfaz de la pestaña de grabación"""
        main_frame = ttk.Frame(self.tab_grabacion, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Panel de control
        control_frame = ttk.LabelFrame(main_frame, text=_("control_grabacion"), padding=10)
        control_frame.pack(fill="x", pady=10)
        
        # Botones de inicio y parada
        botones_frame = ttk.Frame(control_frame)
        botones_frame.pack(fill="x", pady=5)
        
        self.btn_iniciar = ttk.Button(botones_frame, text=_("iniciar_grabacion"), 
                                     command=self.iniciar_grabacion, style="Accent.TButton")
        self.btn_iniciar.pack(side="left", padx=5)
        
        self.btn_detener = ttk.Button(botones_frame, text=_("detener_grabacion"), 
                                     command=self.detener_grabacion, state="disabled")
        self.btn_detener.pack(side="left", padx=5)
        
        # Opciones de intervalo
        opciones_frame = ttk.Frame(control_frame)
        opciones_frame.pack(fill="x", pady=10)
        
        ttk.Label(opciones_frame, text=_("intervalo_grabacion")).pack(side="left", padx=5)
        
        self.intervalo_var = tk.DoubleVar(value=1.0)
        intervalo_spin = ttk.Spinbox(opciones_frame, from_=0.1, to=10.0, increment=0.1,
                                    textvariable=self.intervalo_var, width=5)
        intervalo_spin.pack(side="left", padx=5)
        
        ttk.Label(opciones_frame, text=_("segundos")).pack(side="left", padx=5)
        
        # Panel de estado
        estado_frame = ttk.LabelFrame(main_frame, text=_("estado_grabacion"), padding=10)
        estado_frame.pack(fill="x", pady=10)
        
        # Grid para mostrar información
        self.info_grid = ttk.Frame(estado_frame)
        self.info_grid.pack(fill="x", pady=5)
        
        # Etiquetas para mostrar el estado
        self.estado_labels = {}
        estados = [
            ("estado", _("estado")),
            ("inicio", _("hora_inicio")),
            ("duracion", _("duracion")),
            ("muestras", _("num_muestras"))
        ]
        
        for i, (key, text) in enumerate(estados):
            ttk.Label(self.info_grid, text=f"{text}:", font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=5, pady=2)
            
            self.estado_labels[key] = ttk.Label(self.info_grid, text="--")
            self.estado_labels[key].grid(row=i, column=1, sticky="w", padx=5, pady=2)
        
        # Panel para valores actuales
        valores_frame = ttk.LabelFrame(main_frame, text=_("valores_actuales"), padding=10)
        valores_frame.pack(fill="x", pady=10)
        
        # Grid para valores actuales
        self.valores_grid = ttk.Frame(valores_frame)
        self.valores_grid.pack(fill="x", pady=5)
        
        # Etiquetas para valores actuales
        self.valor_labels = {}
        valores = [
            ("cpu", _("cpu")),
            ("ram", _("ram")),
            ("disco", _("disco")),
            ("red", _("red_mbs"))
        ]
        
        for i, (key, text) in enumerate(valores):
            label_frame = ttk.Frame(self.valores_grid)
            label_frame.grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)
            
            # Icono si está disponible
            if self.iconos.get(key):
                ttk.Label(label_frame, image=self.iconos.get(key)).pack(side="left", padx=(0, 5))
            
            ttk.Label(label_frame, text=f"{text}:", font=("Segoe UI", 10, "bold")).pack(side="left")
            self.valor_labels[key] = ttk.Label(label_frame, text="--")
            self.valor_labels[key].pack(side="left", padx=(5, 0))
        
        # Panel para generar informe
        informe_frame = ttk.LabelFrame(main_frame, text=_("generar_informe"), padding=10)
        informe_frame.pack(fill="x", pady=10)
        
        self.btn_generar = ttk.Button(informe_frame, text=_("generar_pdf"), 
                                     command=self.generar_pdf, state="disabled")
        self.btn_generar.pack(side="top", pady=5)
        
        # Mensaje de ayuda
        ttk.Label(informe_frame, text=_("ayuda_informe"), 
                 font=("Segoe UI", 9), foreground="gray").pack(pady=5)
    
    def iniciar_grabacion(self):
        """Inicia una nueva grabación"""
        # Actualizar intervalo del registrador
        self.registrador.intervalo = self.intervalo_var.get()
        
        if self.registrador.iniciar_grabacion():
            # Actualizar estado de los botones
            self.btn_iniciar.config(state="disabled")
            self.btn_detener.config(state="normal")
            self.btn_generar.config(state="disabled")
            
            # Registrar callback para actualizar UI
            self.registrador.registrar_callback(self.actualizar_ui)
            
            # Actualizar estado inicial
            self.actualizar_estado(iniciando=True)
    
    def detener_grabacion(self):
        """Detiene la grabación actual"""
        if self.registrador.detener_grabacion():
            # Actualizar estado de los botones
            self.btn_iniciar.config(state="normal")
            self.btn_detener.config(state="disabled")
            self.btn_generar.config(state="normal")
            
            # Quitar callback
            self.registrador.quitar_callback(self.actualizar_ui)
            
            # Actualizar estado final
            self.actualizar_estado(finalizando=True)
    
    def actualizar_ui(self, estado):
        """Actualiza la UI con datos del registrador"""
        try:
            # Actualizar valores actuales
            if estado['ultimos_valores']:
                valores = estado['ultimos_valores']
                if 'cpu' in valores and valores['cpu'] is not None:
                    self.valor_labels['cpu'].config(text=f"{valores['cpu']:.1f}%")
                if 'ram' in valores and valores['ram'] is not None:
                    self.valor_labels['ram'].config(text=f"{valores['ram']:.1f}%")
                if 'disco' in valores and valores['disco'] is not None:
                    self.valor_labels['disco'].config(text=f"{valores['disco']:.1f}%")
                if 'red' in valores and valores['red'] is not None:
                    self.valor_labels['red'].config(text=f"{valores['red']:.2f} MB/s")
        except Exception as e:
            print(f"Error al actualizar UI: {e}")
    
    def actualizar_estado(self, iniciando=False, finalizando=False):
        """Actualiza el panel de estado"""
        try:
            estado = self.registrador.obtener_estado()
            
            # Actualizar etiquetas de estado
            if estado['grabando'] or iniciando:
                self.estado_labels['estado'].config(text=_("grabando"), foreground="#00CC00")
            else:
                self.estado_labels['estado'].config(text=_("detenido"), foreground="#CC0000")
            
            # Hora de inicio
            if estado['hora_inicio']:
                self.estado_labels['inicio'].config(
                    text=estado['hora_inicio'].strftime("%d/%m/%Y %H:%M:%S"))
            else:
                self.estado_labels['inicio'].config(text="--")
            
            # Duración
            if estado['duracion']:
                self.estado_labels['duracion'].config(
                    text=str(estado['duracion']).split('.')[0])
            else:
                self.estado_labels['duracion'].config(text="--")
            
            # Número de muestras
            self.estado_labels['muestras'].config(text=str(estado['muestras']))
            
            # Programar próxima actualización solo si está grabando
            if estado['grabando']:
                self.tab_grabacion.after(1000, self.actualizar_estado)
        except Exception as e:
            print(f"Error al actualizar estado: {e}")
            # Reintentar después de un tiempo
            self.tab_grabacion.after(2000, self.actualizar_estado)
    
    def generar_pdf(self):
        """Genera un informe PDF con los datos grabados"""
        try:
            if not self.registrador.datos['timestamp']:
                messagebox.showwarning(_("advertencia"), _("no_datos_informe"))
                return
            
            # Solicitar ruta para guardar el PDF
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                title=_("guardar_informe")
            )
            
            if not ruta_archivo:
                return  # Cancelado por el usuario
            
            # Mostrar diálogo de proceso
            self.mostrar_procesando()
            
            # Generar PDF en un hilo separado para no bloquear la UI
            def generar():
                # Obtener info del sistema para incluir en el informe
                info_sistema = obtener_info_sistema()
                
                resultado, mensaje = self.registrador.generar_pdf(ruta_archivo, info_sistema)
                
                # Actualizar UI en el hilo principal
                self.tab_grabacion.after(0, lambda: self.finalizar_generacion(resultado, mensaje, ruta_archivo))
            
            threading.Thread(target=generar, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror(_("error"), f"{_('error_generar_pdf')}: {str(e)}")
            self.ocultar_procesando()
    
    def mostrar_procesando(self):
        """Muestra un diálogo de procesamiento"""
        self.ventana_proceso = tk.Toplevel(self.tab_grabacion)
        self.ventana_proceso.title(_("procesando"))
        self.ventana_proceso.geometry("300x100")
        self.ventana_proceso.resizable(False, False)
        self.ventana_proceso.transient(self.tab_grabacion)
        self.ventana_proceso.grab_set()
        
        # Centrar ventana
        self.ventana_proceso.geometry("+%d+%d" % (
            self.tab_grabacion.winfo_rootx() + 50,
            self.tab_grabacion.winfo_rooty() + 50
        ))
        
        ttk.Label(self.ventana_proceso, text=_("generando_pdf"), 
                 font=("Segoe UI", 12)).pack(pady=(20, 10))
        
        progress = ttk.Progressbar(self.ventana_proceso, mode='indeterminate')
        progress.pack(padx=20, fill='x')
        progress.start(10)
    
    def ocultar_procesando(self):
        """Oculta el diálogo de procesamiento"""
        if hasattr(self, 'ventana_proceso') and self.ventana_proceso:
            self.ventana_proceso.destroy()
            self.ventana_proceso = None
    
    def finalizar_generacion(self, exito, mensaje, ruta):
        """Finaliza el proceso de generación del PDF"""
        self.ocultar_procesando()
        
        if exito:
            resultado = messagebox.askquestion(_("exito"), 
                                           f"{mensaje}\n\n{_('abrir_pdf_pregunta')}")
            if resultado == "yes":
                self.abrir_pdf(ruta)
        else:
            messagebox.showerror(_("error"), mensaje)
    
    def abrir_pdf(self, ruta):
        """Abre el PDF generado con el visor predeterminado"""
        try:
            import os
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(ruta)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', ruta])
            else:  # Linux
                subprocess.run(['xdg-open', ruta])
        except Exception as e:
            messagebox.showerror(_("error"), f"{_('error_abrir_pdf')}: {str(e)}")

class MonitorSistema:
    """Clase principal de la aplicación
    
    Implementa la interfaz gráfica completa con pestañas para
    información del sistema, procesos, gráficas, configuración
    y grabación de rendimiento"""
    
    def __init__(self):
        self.ventana = tk.Tk()
        self.configurar_ventana()
        self.cargar_iconos()
        self.crear_interfaz()
        self.iniciar_actualizaciones()
    
    def configurar_ventana(self):
        """Configuración inicial de la ventana"""
        self.ventana.title(_("titulo_app"))
        self.ventana.geometry("1250x950")
        self.ventana.minsize(800, 600)
        sv_ttk.set_theme("dark")  # Aplicar tema oscuro de Sun Valley
        
        # Configurar el icono si existe
        try:
            self.ventana.iconbitmap(recurso_ruta("assets/dvi_leon.ico"))
        except:
            pass
        # Añadimos iconos
    def cargar_iconos(self):
        """Carga iconos de forma segura"""
        self.iconos = {}
        iconos_config = {
            "sistema": "assets/system.png",
            "procesos": "assets/processes.png",
            "graficas": "assets/chart.png",
            "config": "assets/config.png",
            "cpu": "assets/cpu.png",
            "ram": "assets/ram.png",
            "disco": "assets/disk.png",
            "red": "assets/network.png",
            "grabacion": "assets/rec.png" 
        }
        
        for nombre, ruta in iconos_config.items():
            try:
                imagen = Image.open(recurso_ruta(ruta))
                if nombre in ["cpu", "ram", "disco", "red"]:
                    imagen = imagen.resize((16, 16))
                else:
                    imagen = imagen.resize((20, 20))
                self.iconos[nombre] = ImageTk.PhotoImage(imagen)
            except:
                # Crear un icono placeholder si falla la carga
                self.iconos[nombre] = None
    
    def crear_interfaz(self):
        """Crea la interfaz principal"""
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill='both', expand=True)
        
        self.crear_tab_sistema()
        self.crear_tab_procesos()
        self.crear_tab_graficas()
        self.crear_tab_configuracion()
        self.crear_tab_grabacion()  # Nueva pestaña de grabación
    
    def crear_tab_grabacion(self):
        """Crear pestaña de grabación de rendimiento"""
        self.tab_grabacion_obj = TabGrabacion(self.notebook, self, self.iconos)
    
    def crear_tab_sistema(self):
        """Crear pestaña de información del sistema"""
        self.tab_sistema = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("sistema"):
            self.notebook.add(self.tab_sistema, text=f" {_('tab_sistema')}", 
                             image=self.iconos.get("sistema"), compound="left")
        else:
            self.notebook.add(self.tab_sistema, text=f" {_('tab_sistema')}")
        
        # Frame principal con scroll
        main_frame = ttk.Frame(self.tab_sistema)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Botón de actualizar
        ttk.Button(main_frame, text=_("actualizar"), 
                  command=self.actualizar_info_sistema).pack(anchor='e', pady=(0, 10))
        
        # Frame para la información
        self.frame_info = ttk.Frame(main_frame)
        self.frame_info.pack(fill="both", expand=True)
        
        self.actualizar_info_sistema()
    
    def actualizar_info_sistema(self):
        """Actualiza la información del sistema"""
        # Limpiar frame anterior
        for widget in self.frame_info.winfo_children():
            widget.destroy()
        
        # Mostrar indicador de carga
        loading_label = ttk.Label(self.frame_info, text=_("obteniendo_info"))
        loading_label.pack()
        
        def cargar_info():
            info = obtener_info_sistema()
            self.ventana.after(0, lambda: self.mostrar_info_sistema(info))
        
        threading.Thread(target=cargar_info, daemon=True).start()
    
    def mostrar_info_sistema(self, info):
        """Muestra la información del sistema en la interfaz"""
        # Limpiar indicador de carga
        for widget in self.frame_info.winfo_children():
            widget.destroy()
        
        fila = 0
        for clave, valor in info.items():
            if clave == "Red":
                ttk.Label(self.frame_info, text=_("interfaces_red"), 
                         font=("Segoe UI", 12, "bold")).grid(column=0, row=fila, sticky='w', pady=5)
                fila += 1
                for interfaz, ip in valor.items():
                    ttk.Label(self.frame_info, text=f"  • {interfaz}: {ip}").grid(
                        column=0, row=fila, sticky='w', padx=20)
                    fila += 1
            else:
                # Frame para cada elemento
                item_frame = ttk.Frame(self.frame_info)
                item_frame.grid(column=0, row=fila, sticky='ew', pady=2)
                self.frame_info.columnconfigure(0, weight=1)
                
                # Mostrar la etiqueta traducida manualmente
                etiqueta = clave
                if clave == "Sistema operativo":
                    etiqueta = _("sistema_operativo")
                elif clave == "Nombre del equipo":
                    etiqueta = _("nombre_equipo")
                elif clave == "Arquitectura":
                    etiqueta = _("arquitectura")
                elif clave == "Procesador":
                    etiqueta = _("procesador")
                elif clave == "RAM total":
                    etiqueta = _("ram_total")
                elif clave == "Disco total":
                    etiqueta = _("disco_total")
                elif clave == "GPU":
                    etiqueta = _("gpu")
                elif clave == "Uptime":
                    etiqueta = _("uptime")
                
                ttk.Label(item_frame, text=f"{etiqueta}:", 
                         font=("Segoe UI", 10, "bold")).pack(side='left')
                ttk.Label(item_frame, text=str(valor)).pack(side='left', padx=(10, 0))
                fila += 1
    
    def crear_tab_procesos(self):
        """Crear pestaña de procesos optimizada"""
        self.tab_procesos = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("procesos"):
            self.notebook.add(self.tab_procesos, text=f" {_('tab_procesos')}", 
                             image=self.iconos.get("procesos"), compound="left")
        else:
            self.notebook.add(self.tab_procesos, text=f" {_('tab_procesos')}")
        
        # Frame de búsqueda mejorado
        frame_busqueda = ttk.Frame(self.tab_procesos)
        frame_busqueda.pack(fill='x', padx=10, pady=5)
        
        # Campo de búsqueda con ayuda
        busqueda_frame = ttk.LabelFrame(frame_busqueda, text=_("busqueda_avanzada"), padding=5)
        busqueda_frame.pack(fill='x')
        
        # Entry de búsqueda
        self.entrada_busqueda = ttk.Entry(busqueda_frame, font=("Segoe UI", 10))
        self.entrada_busqueda.pack(fill='x', pady=2)
        self.entrada_busqueda.bind("<KeyRelease>", self.on_search_change)
        self.entrada_busqueda.bind("<FocusIn>", self.show_search_help)
        
        # Label de ayuda
        self.help_label = ttk.Label(busqueda_frame, 
                                   text=_("ejemplos_busqueda"), 
                                   font=("Segoe UI", 8), foreground="gray")
        self.help_label.pack(anchor='w')
        
        # Controles adicionales
        controls_frame = ttk.Frame(busqueda_frame)
        controls_frame.pack(fill='x', pady=5)
        
        # Botones de filtro rápido
        ttk.Button(controls_frame, text=_("cpu_alto"), 
                  command=lambda: self.set_quick_filter("cpu>50")).pack(side='left', padx=2)
        ttk.Button(controls_frame, text=_("ram_alto"), 
                  command=lambda: self.set_quick_filter("ram>50")).pack(side='left', padx=2)
        ttk.Button(controls_frame, text=_("limpiar"), 
                  command=self.clear_search).pack(side='left', padx=2)
        
        # Información de resultados
        self.info_resultados = ttk.Label(controls_frame, text="")
        self.info_resultados.pack(side='right')
        
        # Tabla de procesos
        cols = (_("pid"), _("nombre"), _("cpu_percent"), _("ram_percent"), _("hilos"))
        self.tree = ttk.Treeview(self.tab_procesos, columns=cols, show='headings', height=25)
        
        # Configurar columnas
        anchos = {_("pid"): 80, _("nombre"): 300, _("cpu_percent"): 100, _("ram_percent"): 100, _("hilos"): 80}
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, anchor='center', width=anchos.get(col, 150))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self.tab_procesos, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.tab_procesos, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        v_scrollbar.pack(side="right", fill="y", pady=10)
        h_scrollbar.pack(side="bottom", fill="x", padx=10)
        
        # Variables para ordenamiento
        self.sort_reverse = False
        self.last_sort_col = None
        
        # Menú contextual
        self.crear_menu_contextual()
        
        # Inicializar vista
        self.actualizar_tabla_procesos()
    
    def crear_menu_contextual(self):
        """Crear menú contextual para procesos"""
        self.menu_contextual = tk.Menu(self.ventana, tearoff=0)
        self.menu_contextual.add_command(label=_("terminar_proceso"), command=self.terminar_proceso)
        self.menu_contextual.add_command(label=_("copiar_pid"), command=self.copiar_pid)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label=_("info_detallada"), command=self.info_proceso)
        
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
    
    def mostrar_menu_contextual(self, event):
        """Mostrar menú contextual"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.menu_contextual.post(event.x_root, event.y_root)
    
    def terminar_proceso(self):
        """Terminar proceso seleccionado"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = self.tree.item(item, 'values')[0]
        nombre = self.tree.item(item, 'values')[1]
        
        if messagebox.askyesno(_("confirmar"), _("pregunta_terminar", nombre, pid)):
            try:
                proceso = psutil.Process(int(pid))
                proceso.terminate()
                messagebox.showinfo(_("exito"), _("proceso_terminado", nombre))
                self.actualizar_tabla_procesos()
            except Exception as e:
                messagebox.showerror(_("error"), _("error_terminar", e))
    
    def copiar_pid(self):
        """Copiar PID al portapapeles"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = self.tree.item(item, 'values')[0]
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(pid)
        messagebox.showinfo(_("copiado"), _("pid_copiado", pid))
    
    def info_proceso(self):
        """Mostrar información detallada del proceso"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = int(self.tree.item(item, 'values')[0])
        
        try:
            proceso = psutil.Process(pid)
            info = _("info_proceso_detalle", 
                     proceso.pid,
                     proceso.name(),
                     proceso.status(),
                     proceso.cpu_percent(),
                     round(proceso.memory_percent(), 2),
                     proceso.num_threads(),
                     datetime.datetime.fromtimestamp(proceso.create_time()),
                     proceso.username() if hasattr(proceso, 'username') else 'N/A'
                    )
            messagebox.showinfo(_("info_proceso_titulo"), info)
        except Exception as e:
            messagebox.showerror(_("error"), f"No se pudo obtener información: {e}")
    
    def on_search_change(self, event):
        """Manejar cambios en el campo de búsqueda"""
        self.actualizar_tabla_procesos()
    
    def show_search_help(self, event):
        """Mostrar ayuda al hacer focus en búsqueda"""
        self.help_label.config(foreground="white")
        self.ventana.after(3000, lambda: self.help_label.config(foreground="gray"))
    
    def set_quick_filter(self, filtro):
        """Establecer filtro rápido"""
        self.entrada_busqueda.delete(0, tk.END)
        self.entrada_busqueda.insert(0, filtro)
        self.actualizar_tabla_procesos()
    
    def clear_search(self):
        """Limpiar búsqueda"""
        self.entrada_busqueda.delete(0, tk.END)
        self.actualizar_tabla_procesos()
    
    def sort_treeview(self, col):
        """Ordenar treeview por columna
        
        Implementa ordenamiento ascendente/descendente y
        detecta si la columna es numérica o texto"""
        if self.last_sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.last_sort_col = col
        
        # Obtener datos y ordenar
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Determinar tipo de ordenamiento
        try:
            # Intentar ordenamiento numérico
            data.sort(key=lambda x: float(x[0].replace('%', '')), reverse=self.sort_reverse)
        except ValueError:
            # Ordenamiento alfabético
            data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        
        # Reordenar items
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # Actualizar indicador de ordenamiento
        for c in self.tree['columns']:
            self.tree.heading(c, text=c)
        
        indicator = " ↓" if self.sort_reverse else " ↑"
        self.tree.heading(col, text=col + indicator)
    
    def actualizar_tabla_procesos(self):
        """Actualizar tabla de procesos de forma optimizada"""
        filtro = self.entrada_busqueda.get()
        
        # Limpiar tabla
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Obtener procesos
        procesos = obtener_procesos_optimizado()
        
        # Aplicar filtro
        if filtro:
            procesos_filtrados = buscar_procesos_avanzada(procesos, filtro)
        else:
            procesos_filtrados = procesos
        
        # Limitar resultados para mejor rendimiento
        max_resultados = 1000
        if len(procesos_filtrados) > max_resultados:
            procesos_filtrados = procesos_filtrados[:max_resultados]
        
        # Insertar en tabla
        for proc in procesos_filtrados:
            self.tree.insert('', tk.END, values=proc)
        
        # Actualizar información de resultados
        total = len(procesos)
        mostrados = len(procesos_filtrados)
        self.info_resultados.config(text=f"{_('mostrando')} {mostrados} {_('de')} {total} {_('procesos')}")
    
    def crear_tab_graficas(self):
        """Crear pestaña de gráficas optimizada"""
        self.tab_graficas = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("graficas"):
            self.notebook.add(self.tab_graficas, text=f" {_('tab_graficas')}", 
                             image=self.iconos.get("graficas"), compound="left")
        else:
            self.notebook.add(self.tab_graficas, text=f" {_('tab_graficas')}")
        
        # Contenedor principal
        contenedor_paneles = ttk.Frame(self.tab_graficas)
        contenedor_paneles.pack(fill='both', expand=True, padx=10, pady=10)
        contenedor_paneles.columnconfigure((0, 1), weight=1)
        contenedor_paneles.rowconfigure((0, 1), weight=1)
        
        # Crear paneles
        self.panel_cpu = ttk.LabelFrame(contenedor_paneles, text=_("cpu"), padding=5)
        self.panel_cpu.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.panel_ram = ttk.LabelFrame(contenedor_paneles, text=_("ram"), padding=5)
        self.panel_ram.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.panel_disco = ttk.LabelFrame(contenedor_paneles, text=_("disco"), padding=5)
        self.panel_disco.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.panel_red = ttk.LabelFrame(contenedor_paneles, text=_("red"), padding=5)
        self.panel_red.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Crear gráficas
        self.crear_grafica(self.panel_cpu, _("cpu"), psutil.cpu_percent, "cpu")
        self.crear_grafica(self.panel_ram, _("ram"), lambda: psutil.virtual_memory().percent, "ram")
        self.crear_grafica(self.panel_disco, _("disco"), lambda: psutil.disk_usage('/').percent, "disco")
        self.crear_grafica(self.panel_red, _("red_mbs"), self.get_network_speed, "red")
        
        # Variables para red
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
    
    def get_network_speed(self):
        """Calcular velocidad de red en MB/s"""
        try:
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            
            if hasattr(self, 'last_net_io'):
                time_diff = current_time - self.last_net_time
                bytes_diff = (current_net_io.bytes_sent + current_net_io.bytes_recv) - \
                           (self.last_net_io.bytes_sent + self.last_net_io.bytes_recv)
                speed_mbps = (bytes_diff / time_diff) / (1024 * 1024)
                
                self.last_net_io = current_net_io
                self.last_net_time = current_time
                
                return min(speed_mbps, 100)  # Limitar para mejor visualización
            else:
                self.last_net_io = current_net_io
                self.last_net_time = current_time
                return 0
        except:
            return 0
    
    def crear_grafica(self, frame, nombre, data_func, color_key):
        """Crear gráfica optimizada
        
        Configura una gráfica matplotlib integrada en Tkinter
        con actualización automática de datos"""
        fig, ax = plt.subplots(figsize=(4.5, 2.5), dpi=100)
        fig.patch.set_facecolor('#2e2e2e')
        ax.set_facecolor('#2e2e2e')
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Datos históricos
        x = list(range(60))
        datos = [0] * 60
        
        def actualizar():
            try:
                # Obtener nuevo dato
                nuevo_dato = data_func()
                datos.pop(0)
                datos.append(nuevo_dato)
                
                # Limpiar y redibujar
                ax.clear()
                ax.set_facecolor('#2e2e2e')
                
                color = grafico_config[color_key + "_color"]
                estilo = grafico_config["estilo"]
                
                if estilo == "line":
                    ax.plot(x, datos, color=color, linewidth=2)
                    ax.fill_between(x, datos, alpha=0.3, color=color)
                else:
                    ax.bar(x, datos, color=color, width=0.8)
                
                # Configurar aspecto
                ax.set_ylim(0, max(100, max(datos) * 1.2) if datos else 100)
                ax.set_title(f"{nombre} - {_('actual')}: {nuevo_dato:.1f}%", 
                           color='white', fontsize=10)
                ax.tick_params(colors='white', labelsize=8)
                ax.grid(True, alpha=0.3)
                
                for spine in ax.spines.values():
                    spine.set_color('white')
                
                canvas.draw()
            except Exception as e:
                print(f"Error actualizando gráfica {nombre}: {e}")
            
            # Programar siguiente actualización
            frame.after(1000, actualizar)
        
        # Iniciar actualizaciones
        actualizar()
        graficas_act[color_key] = actualizar
    
    def crear_tab_configuracion(self):
        """Crear pestaña de configuración"""
        self.tab_config = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("config"):
            self.notebook.add(self.tab_config, text=f" {_('tab_config')}", 
                             image=self.iconos.get("config"), compound="left")
        else:
            self.notebook.add(self.tab_config, text=f" {_('tab_config')}")
        
        # Frame principal
        main_frame = ttk.Frame(self.tab_config, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Configuración de idioma (NUEVO)
        idioma_frame = ttk.LabelFrame(main_frame, text=_("config_idioma"), padding=10)
        idioma_frame.pack(fill="x", pady=10)
        
        ttk.Label(idioma_frame, text=_("seleccionar_idioma"), 
                 font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        # Opciones de idioma
        self.idioma_var = tk.StringVar(value=idioma_actual)
        idioma_opt_frame = ttk.Frame(idioma_frame)
        idioma_opt_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(idioma_opt_frame, text="Español", variable=self.idioma_var, 
                       value="es").pack(side='left', padx=10)
        ttk.Radiobutton(idioma_opt_frame, text="English", variable=self.idioma_var, 
                       value="en").pack(side='left', padx=10)
        
        # Botón para aplicar idioma
        ttk.Button(idioma_frame, text=_("aplicar_idioma"), 
                  command=self.cambiar_idioma).pack(pady=5)
        
        # Configuración de gráficas
        graficas_frame = ttk.LabelFrame(main_frame, text=_("config_graficas"), padding=10)
        graficas_frame.pack(fill="x", pady=10)
        
        # Estilo de gráfica
        self.estilo_var = tk.StringVar(value=grafico_config["estilo"])
        ttk.Label(graficas_frame, text=_("estilo_grafica"), font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        estilo_frame = ttk.Frame(graficas_frame)
        estilo_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(estilo_frame, text=_("linea"), variable=self.estilo_var, 
                       value="line", command=self.cambiar_estilo).pack(side='left', padx=10)
        ttk.Radiobutton(estilo_frame, text=_("barras"), variable=self.estilo_var, 
                       value="bar", command=self.cambiar_estilo).pack(side='left', padx=10)
        
        # Colores de gráficas
        colores_frame = ttk.LabelFrame(main_frame, text=_("colores_graficas"), padding=10)
        colores_frame.pack(fill="x", pady=10)
        
        graficas_colores = [
            ("cpu", _("cpu"), self.iconos.get("cpu")),
            ("ram", _("ram"), self.iconos.get("ram")),
            ("disco", _("disco"), self.iconos.get("disco")),
            ("red", _("red"), self.iconos.get("red"))
        ]
        
        for graf, nombre, icono in graficas_colores:
            frame = ttk.Frame(colores_frame)
            frame.pack(fill='x', pady=2)
            
            # Botón con o sin icono
            if icono:
                ttk.Button(frame, text=_("color_para", nombre), image=icono, compound="left",
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            else:
                ttk.Button(frame, text=_("color_para", nombre),
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            
            # Mostrar color actual
            color_actual = tk.Frame(frame, bg=grafico_config[f"{graf}_color"], 
                                  width=30, height=20)
            color_actual.pack(side='left', padx=10)
        
        # Configuración de rendimiento
        rendimiento_frame = ttk.LabelFrame(main_frame, text=_("config_rendimiento"), padding=10)
        rendimiento_frame.pack(fill="x", pady=10)
        
        ttk.Label(rendimiento_frame, text=_("intervalo_act")).pack(anchor='w')
        self.intervalo_var = tk.DoubleVar(value=2.0)
        intervalo_scale = ttk.Scale(rendimiento_frame, from_=0.5, to=10.0, 
                                  variable=self.intervalo_var, orient="horizontal")
        intervalo_scale.pack(fill='x', pady=5)
        
        self.intervalo_label = ttk.Label(rendimiento_frame, text=f"2.0 {_('segundos')}")
        self.intervalo_label.pack(anchor='w')
        
        def actualizar_intervalo_label(*args):
            valor = self.intervalo_var.get()
            self.intervalo_label.config(text=f"{valor:.1f} {_('segundos')}")
            proceso_cache['cache_duration'] = valor
        
        self.intervalo_var.trace('w', actualizar_intervalo_label)
        
        # Botones de acción
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill='x', pady=20)
        
        ttk.Button(botones_frame, text=_("aplicar_config"), 
                  command=self.aplicar_configuracion).pack(side='left', padx=5)
        ttk.Button(botones_frame, text=_("restaurar_pred"), 
                  command=self.restaurar_predeterminados).pack(side='left', padx=5)
        ttk.Button(botones_frame, text=_("exportar_config"), 
                  command=self.exportar_configuracion).pack(side='left', padx=5)
    
    def cambiar_idioma(self):
        """Cambiar idioma de la aplicación"""
        global idioma_actual
        nuevo_idioma = self.idioma_var.get()
        
        if nuevo_idioma != idioma_actual:
            idioma_actual = nuevo_idioma
            
            # Actualizar títulos de pestañas sin recrearlas
            self.actualizar_titulos_pestanas()
            
            # Actualizar título de ventana
            self.ventana.title(_("titulo_app"))
            
            # Actualizar datos de sistema
            self.actualizar_info_sistema()
            
            # Actualizar procesos
            self.actualizar_tabla_procesos()
            
            # Reconstruir menú contextual
            self.crear_menu_contextual()
            
            # Actualizar los textos de la pestaña de configuración sin recrearla
            self.actualizar_etiquetas_configuracion()
            
            # Notificar al usuario
            messagebox.showinfo(_("idioma_aplicado"), _("reinicio_necesario"))
    
    def actualizar_titulos_pestanas(self):
        """Actualiza solo los títulos de las pestañas sin modificar su estructura"""
        for i, tab in enumerate(self.notebook.tabs()):
            if i == 0:  # Tab Sistema
                self.notebook.tab(tab, text=f" {_('tab_sistema')}")
            elif i == 1:  # Tab Procesos
                self.notebook.tab(tab, text=f" {_('tab_procesos')}")
            elif i == 2:  # Tab Gráficas
                self.notebook.tab(tab, text=f" {_('tab_graficas')}")
            elif i == 3:  # Tab Configuración
                self.notebook.tab(tab, text=f" {_('tab_config')}")
            elif i == 4:  # Tab Grabación
                self.notebook.tab(tab, text=f" {_('tab_grabacion')}")
    
    def actualizar_etiquetas_configuracion(self):
        """Actualiza solo las etiquetas de texto en la pestaña de configuración"""
        # Recorrer solo los widgets existentes y actualizar textos
        try:
            # Actualizar solo textos en los widgets existentes
            for widget in self.tab_config.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.LabelFrame):
                            # Actualizar títulos de LabelFrames por su posición
                            child_text = child.cget("text")
                            if "Idioma" in child_text or "Language" in child_text:
                                child.configure(text=_("config_idioma"))
                            elif "Gráfica" in child_text or "Chart" in child_text or "grafica" in child_text:
                                if "Color" in child_text:
                                    child.configure(text=_("colores_graficas"))
                                else:
                                    child.configure(text=_("config_graficas"))
                            elif "Rendimiento" in child_text or "Performance" in child_text:
                                child.configure(text=_("config_rendimiento"))
                            
                            # Actualizar botones dentro de los frames
                            for elem in child.winfo_children():
                                if isinstance(elem, ttk.Button):
                                    btn_text = elem.cget("text")
                                    if "idioma" in btn_text.lower() or "language" in btn_text.lower():
                                        elem.configure(text=_("aplicar_idioma"))
                                
                                elif isinstance(elem, ttk.Label):
                                    lbl_text = elem.cget("text")
                                    if "idioma" in lbl_text.lower() or "language" in lbl_text.lower():
                                        elem.configure(text=_("seleccionar_idioma"))
                                    elif "estilo" in lbl_text.lower() or "style" in lbl_text.lower():
                                        elem.configure(text=_("estilo_grafica"))
                                    elif "intervalo" in lbl_text.lower() or "interval" in lbl_text.lower():
                                        elem.configure(text=_("intervalo_act"))
                                    elif lbl_text.endswith("segundos") or lbl_text.endswith("seconds"):
                                        valor = float(lbl_text.split()[0])
                                        elem.configure(text=f"{valor:.1f} {_('segundos')}")
            
            # Buscar botones específicos en el frame principal
            for widget in self.tab_config.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):  # Probablemente el frame de botones
                            for btn in child.winfo_children():
                                if isinstance(btn, ttk.Button):
                                    btn_text = btn.cget("text")
                                    if "Aplicar" in btn_text or "Apply" in btn_text:
                                        btn.configure(text=_("aplicar_config"))
                                    elif "Restaurar" in btn_text or "Restore" in btn_text:
                                        btn.configure(text=_("restaurar_pred"))
                                    elif "Exportar" in btn_text or "Export" in btn_text:
                                        btn.configure(text=_("exportar_config"))
        except Exception as e:
            print(f"Error al actualizar etiquetas: {e}")
    
    def cambiar_estilo(self):
        """Cambiar estilo de gráficas"""
        grafico_config["estilo"] = self.estilo_var.get()
        self.aplicar_configuracion()
    
    def elegir_color(self, nombre):
        """Elegir color para gráfica"""
        color = colorchooser.askcolor(title=f"{_('color_para', nombre.upper())}")
        if color[1]:
            grafico_config[nombre + "_color"] = color[1]
            self.aplicar_configuracion()
            # Actualizar color en interfaz
            self.actualizar_colores_interfaz()
    
    def actualizar_colores_interfaz(self):
        """Actualizar colores mostrados en la interfaz"""
        # Esto se podría implementar para actualizar los cuadros de color
        pass
    
    def aplicar_configuracion(self):
        """Aplicar configuración a las gráficas"""
        for clave, funcion in graficas_act.items():
            try:
                funcion()
            except:
                pass
    
    def restaurar_predeterminados(self):
        """Restaurar configuración predeterminada"""
        global grafico_config
        grafico_config = {
            "cpu_color": "#00ff00",
            "ram_color": "#ff6600", 
            "disco_color": "#0099ff",
            "red_color": "#ff0066",
            "estilo": "line"
        }
        self.estilo_var.set("line")
        self.intervalo_var.set(2.0)
        proceso_cache['cache_duration'] = 2.0
        self.aplicar_configuracion()
        messagebox.showinfo(_("aplicar_config"), _("config_restaurada"))
    
    def exportar_configuracion(self):
        """Exportar configuración actual"""
        try:
            import json
            from tkinter import filedialog
            
            config_data = {
                "grafico_config": grafico_config,
                "intervalo_actualizacion": self.intervalo_var.get(),
                "idioma": idioma_actual
            }
            
            archivo = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title=_("guardar_config")
            )
            
            if archivo:
                with open(archivo, 'w') as f:
                    json.dump(config_data, f, indent=4)
                messagebox.showinfo(_("exito"), _("config_guardada", archivo))
        except Exception as e:
            messagebox.showerror(_("error"), _("error_guardar", e))
    
    def iniciar_actualizaciones(self):
        """Iniciar actualizaciones periódicas"""
        def actualizar_procesos_periodicamente():
            if hasattr(self, 'tree'):
                self.actualizar_tabla_procesos()
            self.ventana.after(5000, actualizar_procesos_periodicamente)
        
        # Iniciar actualizaciones después de un breve delay
        self.ventana.after(1000, actualizar_procesos_periodicamente)
    
    def on_closing(self):
        """Manejar cierre de aplicación"""
        try:
            self.ventana.quit()
            self.ventana.destroy()
        except:
            pass
    
    def ejecutar(self):
        """Ejecutar la aplicación"""
        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Mostrar splash screen mientras carga
        self.mostrar_splash()
        
        # Inicializar componentes en background
        threading.Thread(target=self.inicializar_background, daemon=True).start()
        
        self.ventana.mainloop()
    
    def mostrar_splash(self):
        """Mostrar pantalla de carga
        
        Muestra una ventana de bienvenida mientras la aplicación
        carga los componentes necesarios"""
        splash = tk.Toplevel()
        splash.title(_("cargando"))
        splash.geometry("400x200")
        splash.resizable(False, False)
        splash.configure(bg='#2e2e2e')
        
        # Centrar splash
        splash.geometry("+%d+%d" % (
            (splash.winfo_screenwidth()/2 - 200),
            (splash.winfo_screenheight()/2 - 100)
        ))
        
        # Contenido del splash
        ttk.Label(splash, text=_("monitor_sistema"), 
                 font=("Segoe UI", 16, "bold")).pack(pady=30)
        
        self.progress = ttk.Progressbar(splash, mode='indeterminate')
        self.progress.pack(pady=10, padx=50, fill='x')
        self.progress.start(10)
        
        self.status_label = ttk.Label(splash, text=_("iniciando"))
        self.status_label.pack(pady=10)
        
        self.splash = splash
        
        # Cerrar splash después de 3 segundos
        self.ventana.after(3000, self.cerrar_splash)
    
    def cerrar_splash(self):
        """Cerrar pantalla de carga"""
        if hasattr(self, 'splash'):
            self.splash.destroy()
    
    def inicializar_background(self):
        """Inicializar componentes en background
        
        Carga datos del sistema, procesos, etc. en segundo plano
        para no bloquear la interfaz"""
        try:
            # Cargar información inicial
            self.ventana.after(0, lambda: self.status_label.config(text=_("cargando_info")))
            obtener_info_sistema()
            
            self.ventana.after(0, lambda: self.status_label.config(text=_("cargando_procesos")))
            obtener_procesos_optimizado()
            
            self.ventana.after(0, lambda: self.status_label.config(text=_("config_graficas_splash")))
            
            self.ventana.after(0, lambda: self.status_label.config(text=_("listo")))
        except Exception as e:
            print(f"{_('error_fatal', e)}")

# Función principal optimizada
def main():
    """Función principal con manejo de errores
    
    Punto de entrada para la aplicación, verifica dependencias
    y lanza la aplicación principal"""
    try:
        # Verificar dependencias
        try:
            import reportlab
            import pandas
            import numpy
        except ImportError as e:
            print(f"Falta una dependencia: {e}")
            messagebox.showerror(
                "Error de dependencias",
                "Faltan algunas dependencias necesarias para la grabación de rendimiento.\n\n"
                "Por favor instale: reportlab pandas numpy\n\n"
                "Puede hacerlo con: pip install reportlab pandas numpy"
            )
            return
        
        app = MonitorSistema()
        app.ejecutar()
    except KeyboardInterrupt:
        print(_("app_cerrada"))
    except Exception as e:
        print(f"{_('error_fatal', e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()