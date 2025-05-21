
# -*- coding: utf-8 -*-
"""
Monitor del Sistema - Aplicación de Monitoreo en Tiempo Real
============================================================

Una aplicación de escritorio para monitorear el rendimiento del sistema en tiempo real,
incluyendo CPU, RAM, disco, red y procesos activos.

Autor: [Tu nombre]
Versión: 1.0
Licencia: MIT
"""

# === IMPORTACIONES ===
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import psutil                    # Para información del sistema y procesos
import platform                 # Para información del sistema operativo
import cpuinfo                  # Para información detallada del CPU
import GPUtil                   # Para información de la GPU
import socket                   # Para información de red
import shutil                   # Para información del disco
import datetime                 # Para manejo de fechas y tiempo
import matplotlib.pyplot as plt # Para gráficas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Para manejo de imágenes
import threading                # Para ejecución en segundo plano
import sv_ttk                   # Para tema oscuro moderno
import matplotlib
import os
import sys
import time
import re                       # Para expresiones regulares en búsqueda
from concurrent.futures import ThreadPoolExecutor
import queue                    # Para comunicación entre hilos


def recurso_ruta(rel_path):
    """
    Devuelve la ruta absoluta al recurso, sea compilado o no.
    
    Esta función es útil cuando la aplicación se compila con PyInstaller,
    ya que permite acceder a los recursos desde el directorio temporal.
    
    Args:
        rel_path (str): Ruta relativa al recurso
        
    Returns:
        str: Ruta absoluta al recurso
    """
    try:
        # En aplicación compilada, PyInstaller crea _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, usar directorio actual
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)


# === CONFIGURACIÓN DE MATPLOTLIB ===
# Configurar matplotlib cache para evitar problemas con PyInstaller
if hasattr(sys, "_MEIPASS"):
    cache_path = recurso_ruta("matplotlib_cache")
    os.environ["MPLCONFIGDIR"] = cache_path
else:
    os.environ["MPLCONFIGDIR"] = os.path.abspath("./matplotlib_cache")


# === VARIABLES GLOBALES ===

# Cache global para procesos - optimiza rendimiento evitando consultas constantes
proceso_cache = {
    'data': [],                 # Lista de procesos
    'last_update': 0,          # Timestamp de última actualización
    'cache_duration': 2.0      # Duración del cache en segundos
}

# Cola para comunicación entre hilos
update_queue = queue.Queue()

# Configuración gráfica personalizable
grafico_config = {
    "cpu_color": "#00ff00",    # Verde para CPU
    "ram_color": "#ff6600",    # Naranja para RAM
    "disco_color": "#0099ff",  # Azul para Disco
    "red_color": "#ff0066",    # Rosa para Red
    "estilo": "line"           # Estilo de gráfica: "line" o "bar"
}

# Diccionario para guardar referencias a funciones de actualización de gráficas
graficas_act = {}


# === FUNCIONES DE INFORMACIÓN DEL SISTEMA ===

def obtener_info_sistema():
    """
    Obtiene información completa del sistema de forma optimizada.
    
    Recopila datos del sistema operativo, hardware, red, etc.
    Incluye manejo de errores para sistemas que no soporten ciertas funcionalidades.
    
    Returns:
        dict: Diccionario con información del sistema
    """
    try:
        # Información básica del sistema
        uname = platform.uname()
        
        # Obtener CPU info de forma segura (fallback si cpuinfo falla)
        try:
            cpu = cpuinfo.get_cpu_info()['brand_raw']
        except:
            cpu = platform.processor() or "No detectado"
        
        # Información de memoria y disco
        memoria = psutil.virtual_memory()
        disco_total, _, _ = shutil.disk_usage("/")
        
        # Calcular uptime del sistema
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        
        # Optimizar obtención de interfaces de red
        red = {}
        try:
            interfaces = psutil.net_if_addrs()
            for interfaz, direcciones in interfaces.items():
                for dir in direcciones:
                    # Solo IPv4 y no localhost
                    if dir.family == socket.AF_INET and dir.address != '127.0.0.1':
                        red[interfaz] = dir.address
                        break  # Solo tomar la primera IP válida
        except:
            red = {"No disponible": "Error"}
        
        # GPU info optimizada (manejo seguro de errores)
        try:
            gpus = GPUtil.getGPUs()
            gpu_info = gpus[0].name if gpus else "No detectada"
        except:
            gpu_info = "No detectada"
        
        # Retornar diccionario con toda la información
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
    """
    Obtiene lista de procesos de forma optimizada con sistema de cache.
    
    Utiliza un cache para evitar consultas excesivas al sistema,
    mejorando significativamente el rendimiento.
    
    Returns:
        list: Lista de tuplas con información de procesos (PID, nombre, CPU%, RAM%, hilos)
    """
    current_time = time.time()
    
    # Verificar si el cache es válido
    if (current_time - proceso_cache['last_update']) < proceso_cache['cache_duration']:
        return proceso_cache['data']
    
    try:
        procesos = []
        # Atributos a obtener de cada proceso
        attrs = ['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']
        
        # Iterar sobre todos los procesos del sistema
        for p in psutil.process_iter(attrs=attrs):
            try:
                info = p.info
                # Validar que el proceso tenga información válida
                if info['pid'] is not None and info['name']:
                    procesos.append((
                        info['pid'],
                        info['name'],
                        round(info['cpu_percent'] or 0, 1),
                        round(info['memory_percent'] or 0, 1),
                        info['num_threads'] or 0
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Ignorar procesos que ya no existen o sin permisos
                continue
        
        # Ordenar por uso de CPU (descendente) y actualizar cache
        proceso_cache['data'] = sorted(procesos, key=lambda x: x[2], reverse=True)
        proceso_cache['last_update'] = current_time
        
        return proceso_cache['data']
    except Exception as e:
        print(f"Error obteniendo procesos: {e}")
        return []


def buscar_procesos_avanzada(procesos, filtro):
    """
    Búsqueda avanzada de procesos con regex y múltiples criterios.
    
    Soporta búsqueda por:
    - PID específico
    - Nombre del proceso (con regex)
    - Filtros de CPU/RAM (ej: "cpu>50", "ram<10")
    
    Args:
        procesos (list): Lista de procesos
        filtro (str): Cadena de filtro
        
    Returns:
        list: Lista filtrada de procesos
    """
    if not filtro:
        return procesos
    
    filtro = filtro.lower().strip()
    resultados = []
    
    # Verificar si es un PID numérico
    if filtro.isdigit():
        pid_filtro = int(filtro)
        for proc in procesos:
            if proc[0] == pid_filtro:
                resultados.append(proc)
        return resultados
    
    # Verificar filtros de rendimiento con regex
    cpu_match = re.match(r'cpu([<>]=?)(\d+(?:\.\d+)?)', filtro)
    ram_match = re.match(r'ram([<>]=?)(\d+(?:\.\d+)?)', filtro)
    
    # Filtro por CPU
    if cpu_match:
        op, valor = cpu_match.groups()
        valor = float(valor)
        for proc in procesos:
            if evaluar_condicion(proc[2], op, valor):
                resultados.append(proc)
        return resultados
    
    # Filtro por RAM
    if ram_match:
        op, valor = ram_match.groups()
        valor = float(valor)
        for proc in procesos:
            if evaluar_condicion(proc[3], op, valor):
                resultados.append(proc)
        return resultados
    
    # Búsqueda por nombre con soporte regex
    try:
        # Intentar compilar como expresión regular
        patron = re.compile(filtro, re.IGNORECASE)
        for proc in procesos:
            if patron.search(proc[1]):
                resultados.append(proc)
    except re.error:
        # Si falla regex, realizar búsqueda simple
        for proc in procesos:
            if filtro in proc[1].lower():
                resultados.append(proc)
    
    return resultados


def evaluar_condicion(valor, operador, referencia):
    """
    Evalúa condiciones matemáticas para filtros numéricos.
    
    Args:
        valor (float): Valor a evaluar
        operador (str): Operador de comparación (>, <, >=, <=)
        referencia (float): Valor de referencia
        
    Returns:
        bool: Resultado de la evaluación
    """
    if operador == '>':
        return valor > referencia
    elif operador == '<':
        return valor < referencia
    elif operador == '>=':
        return valor >= referencia
    elif operador == '<=':
        return valor <= referencia
    return False


# === CLASE PRINCIPAL ===

class MonitorSistema:
    """
    Clase principal que maneja la interfaz gráfica y funcionalidad del monitor.
    
    Implementa una aplicación de escritorio con pestañas para:
    - Información del sistema
    - Lista de procesos con búsqueda avanzada
    - Gráficas en tiempo real
    - Configuración personalizable
    """
    
    def __init__(self):
        """Inicializar la aplicación y sus componentes."""
        self.ventana = tk.Tk()
        self.configurar_ventana()
        self.cargar_iconos()
        self.crear_interfaz()
        self.iniciar_actualizaciones()
    
    def configurar_ventana(self):
        """Configuración inicial de la ventana principal."""
        self.ventana.title("Monitor del Sistema - Optimizado")
        self.ventana.geometry("1250x950")
        self.ventana.minsize(800, 600)
        
        # Aplicar tema oscuro moderno
        sv_ttk.set_theme("dark")
        
        # Configurar el icono de la aplicación si existe
        try:
            self.ventana.iconbitmap(recurso_ruta("assets/dvi_leon.ico"))
        except:
            pass  # Ignorar si no existe el icono
    
    def cargar_iconos(self):
        """
        Carga iconos de forma segura con fallbacks.
        
        Intenta cargar iconos desde archivos PNG, si falla crea placeholders.
        Los iconos se redimensionan según su uso.
        """
        self.iconos = {}
        
        # Configuración de iconos con sus rutas
        iconos_config = {
            "sistema": "assets/system.png",
            "procesos": "assets/processes.png",
            "graficas": "assets/chart.png",
            "config": "assets/config.png",
            "cpu": "assets/cpu.png",
            "ram": "assets/ram.png",
            "disco": "assets/disk.png",
            "red": "assets/network.png",
        }
        
        # Cargar cada icono con manejo de errores
        for nombre, ruta in iconos_config.items():
            try:
                imagen = Image.open(recurso_ruta(ruta))
                
                # Redimensionar según el tipo de icono
                if nombre in ["cpu", "ram", "disco", "red"]:
                    imagen = imagen.resize((16, 16))
                else:
                    imagen = imagen.resize((20, 20))
                
                self.iconos[nombre] = ImageTk.PhotoImage(imagen)
            except:
                # Si falla la carga, usar None (sin icono)
                self.iconos[nombre] = None
    
    def crear_interfaz(self):
        """Crea la interfaz principal con sistema de pestañas."""
        # Crear notebook (contenedor de pestañas)
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill='both', expand=True)
        
        # Crear todas las pestañas
        self.crear_tab_sistema()
        self.crear_tab_procesos()
        self.crear_tab_graficas()
        self.crear_tab_configuracion()
    
    # === PESTAÑA DE INFORMACIÓN DEL SISTEMA ===
    
    def crear_tab_sistema(self):
        """Crear pestaña de información del sistema."""
        self.tab_sistema = ttk.Frame(self.notebook)
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("sistema"):
            self.notebook.add(self.tab_sistema, text=' Sistema', 
                             image=self.iconos.get("sistema"), compound="left")
        else:
            self.notebook.add(self.tab_sistema, text=' Sistema')
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.tab_sistema)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Botón de actualización
        ttk.Button(main_frame, text="Actualizar información", 
                  command=self.actualizar_info_sistema).pack(anchor='e', pady=(0, 10))
        
        # Frame contenedor para la información
        self.frame_info = ttk.Frame(main_frame)
        self.frame_info.pack(fill="both", expand=True)
        
        # Cargar información inicial
        self.actualizar_info_sistema()
    
    def actualizar_info_sistema(self):
        """Actualiza la información del sistema en segundo plano."""
        # Limpiar contenido anterior
        for widget in self.frame_info.winfo_children():
            widget.destroy()
        
        # Mostrar indicador de carga
        loading_label = ttk.Label(self.frame_info, text="Obteniendo información del sistema...")
        loading_label.pack()
        
        def cargar_info():
            """Función para cargar información en hilo separado."""
            info = obtener_info_sistema()
            # Programar actualización en hilo principal
            self.ventana.after(0, lambda: self.mostrar_info_sistema(info))
        
        # Ejecutar carga en hilo separado
        threading.Thread(target=cargar_info, daemon=True).start()
    
    def mostrar_info_sistema(self, info):
        """
        Muestra la información del sistema en la interfaz.
        
        Args:
            info (dict): Diccionario con información del sistema
        """
        # Limpiar indicador de carga
        for widget in self.frame_info.winfo_children():
            widget.destroy()
        
        fila = 0
        for clave, valor in info.items():
            if clave == "Red":
                # Tratamiento especial para interfaces de red
                ttk.Label(self.frame_info, text="Interfaces de red:", 
                         font=("Segoe UI", 12, "bold")).grid(column=0, row=fila, sticky='w', pady=5)
                fila += 1
                
                # Mostrar cada interfaz
                for interfaz, ip in valor.items():
                    ttk.Label(self.frame_info, text=f"  • {interfaz}: {ip}").grid(
                        column=0, row=fila, sticky='w', padx=20)
                    fila += 1
            else:
                # Frame para cada elemento de información
                item_frame = ttk.Frame(self.frame_info)
                item_frame.grid(column=0, row=fila, sticky='ew', pady=2)
                self.frame_info.columnconfigure(0, weight=1)
                
                # Etiqueta y valor
                ttk.Label(item_frame, text=f"{clave}:", 
                         font=("Segoe UI", 10, "bold")).pack(side='left')
                ttk.Label(item_frame, text=str(valor)).pack(side='left', padx=(10, 0))
                fila += 1
    
    # === PESTAÑA DE PROCESOS ===
    
    def crear_tab_procesos(self):
        """Crear pestaña de procesos con búsqueda avanzada."""
        self.tab_procesos = ttk.Frame(self.notebook)
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("procesos"):
            self.notebook.add(self.tab_procesos, text=' Procesos', 
                             image=self.iconos.get("procesos"), compound="left")
        else:
            self.notebook.add(self.tab_procesos, text=' Procesos')
        
        # === SECCIÓN DE BÚSQUEDA ===
        frame_busqueda = ttk.Frame(self.tab_procesos)
        frame_busqueda.pack(fill='x', padx=10, pady=5)
        
        # Frame de búsqueda con ayuda
        busqueda_frame = ttk.LabelFrame(frame_busqueda, text="Búsqueda avanzada", padding=5)
        busqueda_frame.pack(fill='x')
        
        # Campo de entrada para búsqueda
        self.entrada_busqueda = ttk.Entry(busqueda_frame, font=("Segoe UI", 10))
        self.entrada_busqueda.pack(fill='x', pady=2)
        self.entrada_busqueda.bind("<KeyRelease>", self.on_search_change)
        self.entrada_busqueda.bind("<FocusIn>", self.show_search_help)
        
        # Etiqueta de ayuda para la búsqueda
        self.help_label = ttk.Label(busqueda_frame, 
                                   text="💡 Ejemplos: 'chrome', 'cpu>50', 'ram<10', PID numérico", 
                                   font=("Segoe UI", 8), foreground="gray")
        self.help_label.pack(anchor='w')
        
        # === CONTROLES ADICIONALES ===
        controls_frame = ttk.Frame(busqueda_frame)
        controls_frame.pack(fill='x', pady=5)
        
        # Botones de filtro rápido
        ttk.Button(controls_frame, text="CPU Alto (>50%)", 
                  command=lambda: self.set_quick_filter("cpu>50")).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="RAM Alto (>50%)", 
                  command=lambda: self.set_quick_filter("ram>50")).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="Limpiar", 
                  command=self.clear_search).pack(side='left', padx=2)
        
        # Información de resultados
        self.info_resultados = ttk.Label(controls_frame, text="")
        self.info_resultados.pack(side='right')
        
        # === TABLA DE PROCESOS ===
        cols = ("PID", "Nombre", "CPU %", "RAM %", "Hilos")
        self.tree = ttk.Treeview(self.tab_procesos, columns=cols, show='headings', height=25)
        
        # Configurar columnas con anchos específicos
        anchos = {"PID": 80, "Nombre": 300, "CPU %": 100, "RAM %": 100, "Hilos": 80}
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, anchor='center', width=anchos.get(col, 150))
        
        # Barras de desplazamiento
        v_scrollbar = ttk.Scrollbar(self.tab_procesos, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.tab_procesos, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Posicionar widgets
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        v_scrollbar.pack(side="right", fill="y", pady=10)
        h_scrollbar.pack(side="bottom", fill="x", padx=10)
        
        # Variables para el sistema de ordenamiento
        self.sort_reverse = False
        self.last_sort_col = None
        
        # Crear menú contextual
        self.crear_menu_contextual()
        
        # Cargar datos iniciales
        self.actualizar_tabla_procesos()
    
    def crear_menu_contextual(self):
        """Crear menú contextual para operaciones con procesos."""
        self.menu_contextual = tk.Menu(self.ventana, tearoff=0)
        self.menu_contextual.add_command(label="Terminar proceso", command=self.terminar_proceso)
        self.menu_contextual.add_command(label="Copiar PID", command=self.copiar_pid)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Información detallada", command=self.info_proceso)
        
        # Bind para mostrar menú con click derecho
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
    
    def mostrar_menu_contextual(self, event):
        """Mostrar menú contextual en la posición del cursor."""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.menu_contextual.post(event.x_root, event.y_root)
    
    def terminar_proceso(self):
        """Terminar el proceso seleccionado con confirmación."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = self.tree.item(item, 'values')[0]
        nombre = self.tree.item(item, 'values')[1]
        
        # Confirmar acción
        if messagebox.askyesno("Confirmar", f"¿Terminar proceso {nombre} (PID: {pid})?"):
            try:
                proceso = psutil.Process(int(pid))
                proceso.terminate()
                messagebox.showinfo("Éxito", f"Proceso {nombre} terminado")
                self.actualizar_tabla_procesos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo terminar el proceso: {e}")
    
    def copiar_pid(self):
        """Copiar PID del proceso seleccionado al portapapeles."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = self.tree.item(item, 'values')[0]
        
        # Copiar al portapapeles
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(pid)
        messagebox.showinfo("Copiado", f"PID {pid} copiado al portapapeles")
    
    def info_proceso(self):
        """Mostrar información detallada del proceso seleccionado."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = int(self.tree.item(item, 'values')[0])
        
        try:
            proceso = psutil.Process(pid)
            # Recopilar información detallada
            info = f"""Información del proceso:
            
PID: {proceso.pid}
Nombre: {proceso.name()}
Estado: {proceso.status()}
CPU: {proceso.cpu_percent()}%
Memoria: {round(proceso.memory_percent(), 2)}%
Hilos: {proceso.num_threads()}
Creado: {datetime.datetime.fromtimestamp(proceso.create_time())}
Usuario: {proceso.username() if hasattr(proceso, 'username') else 'N/A'}
"""
            messagebox.showinfo("Información del proceso", info)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener información: {e}")
    
    # === FUNCIONES DE BÚSQUEDA Y FILTRADO ===
    
    def on_search_change(self, event):
        """Manejar cambios en el campo de búsqueda en tiempo real."""
        self.actualizar_tabla_procesos()
    
    def show_search_help(self, event):
        """Mostrar ayuda temporalmente al enfocar el campo de búsqueda."""
        self.help_label.config(foreground="white")
        # Ocultar ayuda después de 3 segundos
        self.ventana.after(3000, lambda: self.help_label.config(foreground="gray"))
    
    def set_quick_filter(self, filtro):
        """Establecer filtro rápido predefinido."""
        self.entrada_busqueda.delete(0, tk.END)
        self.entrada_busqueda.insert(0, filtro)
        self.actualizar_tabla_procesos()
    
    def clear_search(self):
        """Limpiar el campo de búsqueda."""
        self.entrada_busqueda.delete(0, tk.END)
        self.actualizar_tabla_procesos()
    
    def sort_treeview(self, col):
        """
        Ordenar treeview por columna seleccionada.
        
        Alterna entre orden ascendente y descendente.
        Detecta automáticamente tipo de datos (numérico vs alfabético).
        """
        # Determinar dirección de ordenamiento
        if self.last_sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.last_sort_col = col
        
        # Obtener datos para ordenar
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Determinar tipo de ordenamiento
        try:
            # Intentar ordenamiento numérico (quitar % si existe)
            data.sort(key=lambda x: float(x[0].replace('%', '')), reverse=self.sort_reverse)
        except ValueError:
            # Fallback a ordenamiento alfabético
            data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        
        # Reordenar elementos en el treeview
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # Actualizar indicadores visuales de ordenamiento
        for c in self.tree['columns']:
            self.tree.heading(c, text=c)
        
        # Agregar flecha indicadora
        indicator = " ↓" if self.sort_reverse else " ↑"
        self.tree.heading(col, text=col + indicator)
    
    def actualizar_tabla_procesos(self):
        """Actualizar tabla de procesos con filtros aplicados."""
        filtro = self.entrada_busqueda.get()
        
        # Limpiar tabla actual
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Obtener procesos (con cache)
        procesos = obtener_procesos_optimizado()
        
        # Aplicar filtro si existe
        if filtro:
            procesos_filtrados = buscar_procesos_avanzada(procesos, filtro)
        else:
            procesos_filtrados = procesos
        
        # Limitar resultados para mejor rendimiento
        max_resultados = 1000
        if len(procesos_filtrados) > max_resultados:
            procesos_filtrados = procesos_filtrados[:max_resultados]
        
        # Insertar procesos en la tabla
        for proc in procesos_filtrados:
            self.tree.insert('', tk.END, values=proc)
        
        # Actualizar contador de resultados
        total = len(procesos)
        mostrados = len(procesos_filtrados)
        self.info_resultados.config(text=f"Mostrando {mostrados} de {total} procesos")
    
    # === PESTAÑA DE GRÁFICAS ===
    
    def crear_tab_graficas(self):
        """Crear pestaña de gráficas de rendimiento en tiempo real."""
        self.tab_graficas = ttk.Frame(self.notebook)
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("graficas"):
            self.notebook.add(self.tab_graficas, text=' Gráficas', 
                             image=self.iconos.get("graficas"), compound="left")
        else:
            self.notebook.add(self.tab_graficas, text=' Gráficas')
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("graficas"):
            # Si existe el icono de gráficas, lo agrega junto al texto de la pestaña
            self.notebook.add(self.tab_graficas, text=' Gráficas', 
                             image=self.iconos.get("graficas"), compound="left")
        else:
            # Si no hay icono disponible, solo agrega el texto
            self.notebook.add(self.tab_graficas, text=' Gráficas')
        
        # Crear contenedor principal para organizar las gráficas en una cuadrícula 2x2
        contenedor_paneles = ttk.Frame(self.tab_graficas)
        contenedor_paneles.pack(fill='both', expand=True, padx=10, pady=10)
        # Configurar que ambas columnas y filas se expandan proporcionalmente
        contenedor_paneles.columnconfigure((0, 1), weight=1)
        contenedor_paneles.rowconfigure((0, 1), weight=1)
        
        # Crear los cuatro paneles para diferentes métricas del sistema
        # Panel superior izquierdo: CPU
        self.panel_cpu = ttk.LabelFrame(contenedor_paneles, text="CPU", padding=5)
        self.panel_cpu.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Panel superior derecho: RAM
        self.panel_ram = ttk.LabelFrame(contenedor_paneles, text="RAM", padding=5)
        self.panel_ram.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Panel inferior izquierdo: Disco
        self.panel_disco = ttk.LabelFrame(contenedor_paneles, text="Disco", padding=5)
        self.panel_disco.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Panel inferior derecho: Red
        self.panel_red = ttk.LabelFrame(contenedor_paneles, text="Red", padding=5)
        self.panel_red.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Crear las gráficas individuales con sus respectivas funciones de obtención de datos
        self.crear_grafica(self.panel_cpu, "CPU", psutil.cpu_percent, "cpu")
        self.crear_grafica(self.panel_ram, "RAM", lambda: psutil.virtual_memory().percent, "ram")
        self.crear_grafica(self.panel_disco, "Disco", lambda: psutil.disk_usage('/').percent, "disco")
        self.crear_grafica(self.panel_red, "Red (MB/s)", self.get_network_speed, "red")
        
        # Inicializar variables para el cálculo de velocidad de red
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
    
    def get_network_speed(self):
        """Calcular velocidad de red en MB/s"""
        try:
            # Obtener estadísticas actuales de red
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # Si ya tenemos mediciones anteriores, calcular la velocidad
            if hasattr(self, 'last_net_io'):
                # Calcular diferencia de tiempo transcurrido
                time_diff = current_time - self.last_net_time
                # Calcular diferencia de bytes transferidos (enviados + recibidos)
                bytes_diff = (current_net_io.bytes_sent + current_net_io.bytes_recv) - \
                           (self.last_net_io.bytes_sent + self.last_net_io.bytes_recv)
                # Convertir a MB/s
                speed_mbps = (bytes_diff / time_diff) / (1024 * 1024)
                
                # Actualizar valores para la próxima medición
                self.last_net_io = current_net_io
                self.last_net_time = current_time
                
                # Limitar el valor máximo para mejor visualización en la gráfica
                return min(speed_mbps, 100)
            else:
                # Primera medición, solo guardar valores iniciales
                self.last_net_io = current_net_io
                self.last_net_time = current_time
                return 0
        except:
            # En caso de error, retornar 0
            return 0
    
    def crear_grafica(self, frame, nombre, data_func, color_key):
        """Crear gráfica optimizada para mostrar métricas en tiempo real"""
        # Crear figura de matplotlib con fondo oscuro
        fig, ax = plt.subplots(figsize=(4.5, 2.5), dpi=100)
        fig.patch.set_facecolor('#2e2e2e')  # Fondo de la figura
        ax.set_facecolor('#2e2e2e')         # Fondo del área de trazado
        
        # Integrar la gráfica en tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Inicializar datos históricos (últimos 60 puntos)
        x = list(range(60))  # Eje X (60 mediciones)
        datos = [0] * 60     # Eje Y (valores iniciales en 0)
        
        def actualizar():
            """Función interna para actualizar la gráfica periódicamente"""
            try:
                # Obtener nueva medición usando la función proporcionada
                nuevo_dato = data_func()
                # Desplazar datos (FIFO: quitar el más antiguo, agregar el nuevo)
                datos.pop(0)
                datos.append(nuevo_dato)
                
                # Limpiar gráfica anterior
                ax.clear()
                ax.set_facecolor('#2e2e2e')
                
                # Obtener configuración de color y estilo
                color = grafico_config[color_key + "_color"]
                estilo = grafico_config["estilo"]
                
                # Dibujar según el estilo configurado
                if estilo == "line":
                    # Gráfica de línea con relleno
                    ax.plot(x, datos, color=color, linewidth=2)
                    ax.fill_between(x, datos, alpha=0.3, color=color)
                else:
                    # Gráfica de barras
                    ax.bar(x, datos, color=color, width=0.8)
                
                # Configurar aspecto visual
                # Establecer límites del eje Y (0 a 100% o al máximo de los datos)
                ax.set_ylim(0, max(100, max(datos) * 1.2) if datos else 100)
                # Título con valor actual
                ax.set_title(f"{nombre} - Actual: {nuevo_dato:.1f}%", 
                           color='white', fontsize=10)
                # Estilo de los ticks
                ax.tick_params(colors='white', labelsize=8)
                # Grilla sutil
                ax.grid(True, alpha=0.3)
                
                # Establecer color blanco para los bordes
                for spine in ax.spines.values():
                    spine.set_color('white')
                
                # Actualizar el canvas
                canvas.draw()
            except Exception as e:
                print(f"Error actualizando gráfica {nombre}: {e}")
            
            # Programar la siguiente actualización en 1 segundo
            frame.after(1000, actualizar)
        
        # Iniciar el ciclo de actualizaciones
        actualizar()
        # Registrar la función de actualización para poder llamarla desde configuración
        graficas_act[color_key] = actualizar
    
    def crear_tab_configuracion(self):
        """Crear pestaña de configuración para personalizar la aplicación"""
        self.tab_config = ttk.Frame(self.notebook)
        
        # Agregar pestaña con icono si está disponible
        if self.iconos.get("config"):
            self.notebook.add(self.tab_config, text=' Configuración', 
                             image=self.iconos.get("config"), compound="left")
        else:
            self.notebook.add(self.tab_config, text=' Configuración')
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.tab_config, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # --- SECCIÓN: Configuración de gráficas ---
        graficas_frame = ttk.LabelFrame(main_frame, text="Configuración de gráficas", padding=10)
        graficas_frame.pack(fill="x", pady=10)
        
        # Selector de estilo de gráfica (línea vs barras)
        self.estilo_var = tk.StringVar(value=grafico_config["estilo"])
        ttk.Label(graficas_frame, text="Estilo de gráfica:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        estilo_frame = ttk.Frame(graficas_frame)
        estilo_frame.pack(fill='x', pady=5)
        
        # Radio buttons para seleccionar estilo
        ttk.Radiobutton(estilo_frame, text="Línea", variable=self.estilo_var, 
                       value="line", command=self.cambiar_estilo).pack(side='left', padx=10)
        ttk.Radiobutton(estilo_frame, text="Barras", variable=self.estilo_var, 
                       value="bar", command=self.cambiar_estilo).pack(side='left', padx=10)
        
        # --- SECCIÓN: Colores de gráficas ---
        colores_frame = ttk.LabelFrame(main_frame, text="Colores de gráficas", padding=10)
        colores_frame.pack(fill="x", pady=10)
        
        # Lista de gráficas con sus iconos correspondientes
        graficas_colores = [
            ("cpu", "CPU", self.iconos.get("cpu")),
            ("ram", "RAM", self.iconos.get("ram")),
            ("disco", "Disco", self.iconos.get("disco")),
            ("red", "Red", self.iconos.get("red"))
        ]
        
        # Crear botones de selección de color para cada gráfica
        for graf, nombre, icono in graficas_colores:
            frame = ttk.Frame(colores_frame)
            frame.pack(fill='x', pady=2)
            
            # Botón para elegir color (con icono si está disponible)
            if icono:
                ttk.Button(frame, text=f"Color {nombre}", image=icono, compound="left",
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            else:
                ttk.Button(frame, text=f"Color {nombre}",
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            
            # Muestra del color actual
            color_actual = tk.Frame(frame, bg=grafico_config[f"{graf}_color"], 
                                  width=30, height=20)
            color_actual.pack(side='left', padx=10)
        
        # --- SECCIÓN: Configuración de rendimiento ---
        rendimiento_frame = ttk.LabelFrame(main_frame, text="Configuración de rendimiento", padding=10)
        rendimiento_frame.pack(fill="x", pady=10)
        
        # Control deslizante para intervalo de actualización
        ttk.Label(rendimiento_frame, text="Intervalo de actualización (segundos):").pack(anchor='w')
        self.intervalo_var = tk.DoubleVar(value=2.0)
        intervalo_scale = ttk.Scale(rendimiento_frame, from_=0.5, to=10.0, 
                                  variable=self.intervalo_var, orient="horizontal")
        intervalo_scale.pack(fill='x', pady=5)
        
        # Label que muestra el valor actual del intervalo
        self.intervalo_label = ttk.Label(rendimiento_frame, text="2.0 segundos")
        self.intervalo_label.pack(anchor='w')
        
        def actualizar_intervalo_label(*args):
            """Actualizar el label cuando cambia el valor del intervalo"""
            valor = self.intervalo_var.get()
            self.intervalo_label.config(text=f"{valor:.1f} segundos")
            # Actualizar también la duración del cache de procesos
            proceso_cache['cache_duration'] = valor
        
        # Vincular el cambio del slider con la actualización del label
        self.intervalo_var.trace('w', actualizar_intervalo_label)
        
        # --- SECCIÓN: Botones de acción ---
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill='x', pady=20)
        
        # Botones para gestionar la configuración
        ttk.Button(botones_frame, text="Aplicar configuración", 
                  command=self.aplicar_configuracion).pack(side='left', padx=5)
        ttk.Button(botones_frame, text="Restaurar predeterminados", 
                  command=self.restaurar_predeterminados).pack(side='left', padx=5)
        ttk.Button(botones_frame, text="Exportar configuración", 
                  command=self.exportar_configuracion).pack(side='left', padx=5)
    
    def cambiar_estilo(self):
        """Cambiar el estilo de todas las gráficas"""
        # Actualizar la configuración global con el nuevo estilo
        grafico_config["estilo"] = self.estilo_var.get()
        # Aplicar inmediatamente el cambio a todas las gráficas
        self.aplicar_configuracion()
    
    def elegir_color(self, nombre):
        """Abrir diálogo para elegir color de una gráfica específica"""
        # Abrir selector de color
        color = colorchooser.askcolor(title=f"Seleccionar color para {nombre.upper()}")
        if color[1]:  # Si se seleccionó un color (color[1] es el código hexadecimal)
            # Actualizar la configuración con el nuevo color
            grafico_config[nombre + "_color"] = color[1]
            # Aplicar el cambio inmediatamente
            self.aplicar_configuracion()
            # Actualizar la interfaz para mostrar el nuevo color
            self.actualizar_colores_interfaz()
    
    def actualizar_colores_interfaz(self):
        """Actualizar los cuadros de color mostrados en la interfaz de configuración"""
        # Esta función podría implementarse para actualizar visualmente
        # los cuadros de color en la pestaña de configuración
        # Por ahora es un placeholder
        pass
    
    def aplicar_configuracion(self):
        """Aplicar la configuración actual a todas las gráficas activas"""
        # Recorrer todas las gráficas registradas y forzar su actualización
        for clave, funcion in graficas_act.items():
            try:
                funcion()  # Llamar a la función de actualización de cada gráfica
            except:
                pass  # Ignorar errores silenciosamente
    
    def restaurar_predeterminados(self):
        """Restaurar toda la configuración a sus valores predeterminados"""
        global grafico_config
        # Resetear configuración de gráficas a valores por defecto
        grafico_config = {
            "cpu_color": "#00ff00",     # Verde para CPU
            "ram_color": "#ff6600",     # Naranja para RAM 
            "disco_color": "#0099ff",   # Azul para disco
            "red_color": "#ff0066",     # Rosa para red
            "estilo": "line"            # Estilo línea por defecto
        }
        # Resetear controles de la interfaz
        self.estilo_var.set("line")
        self.intervalo_var.set(2.0)
        proceso_cache['cache_duration'] = 2.0
        # Aplicar los cambios
        self.aplicar_configuracion()
        # Mostrar confirmación
        messagebox.showinfo("Configuración", "Configuración restaurada a valores predeterminados")
    
    def exportar_configuracion(self):
        """Exportar la configuración actual a un archivo JSON"""
        try:
            import json
            from tkinter import filedialog
            
            # Preparar datos de configuración para exportar
            config_data = {
                "grafico_config": grafico_config,
                "intervalo_actualizacion": self.intervalo_var.get()
            }
            
            # Abrir diálogo para seleccionar ubicación del archivo
            archivo = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Guardar configuración"
            )
            
            # Si se seleccionó un archivo, guardarlo
            if archivo:
                with open(archivo, 'w') as f:
                    json.dump(config_data, f, indent=4)
                messagebox.showinfo("Éxito", f"Configuración guardada en {archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")
    
    def iniciar_actualizaciones(self):
        """Iniciar el sistema de actualizaciones periódicas de la aplicación"""
        def actualizar_procesos_periodicamente():
            """Función que se ejecuta periódicamente para actualizar la tabla de procesos"""
            # Verificar que la tabla de procesos exista antes de actualizarla
            if hasattr(self, 'tree'):
                self.actualizar_tabla_procesos()
            # Programar la siguiente actualización en 5 segundos
            self.ventana.after(5000, actualizar_procesos_periodicamente)
        
        # Iniciar las actualizaciones después de un breve delay inicial
        # para dar tiempo a que la interfaz se cargue completamente
        self.ventana.after(1000, actualizar_procesos_periodicamente)
    
    def on_closing(self):
        """Manejar el cierre correcto de la aplicación"""
        try:
            # Terminar el bucle principal de tkinter
            self.ventana.quit()
            # Destruir la ventana y liberar recursos
            self.ventana.destroy()
        except:
            # Ignorar errores al cerrar (la aplicación puede estar ya cerrada)
            pass
    
    def ejecutar(self):
        """Ejecutar la aplicación principal"""
        # Configurar el manejador para el cierre de ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Mostrar pantalla de carga mientras se inicializa la aplicación
        self.mostrar_splash()
        
        # Inicializar componentes pesados en background
        threading.Thread(target=self.inicializar_background, daemon=True).start()
        
        # Iniciar el bucle principal de la GUI
        self.ventana.mainloop()
    
    def mostrar_splash(self):
        """Mostrar pantalla de carga inicial"""
        # Crear ventana splash
        splash = tk.Toplevel()
        splash.title("Cargando...")
        splash.geometry("400x200")
        splash.resizable(False, False)
        splash.configure(bg='#2e2e2e')
        
        # Centrar la ventana splash en la pantalla
        splash.geometry("+%d+%d" % (
            (splash.winfo_screenwidth()/2 - 200),
            (splash.winfo_screenheight()/2 - 100)
        ))
        
        # Contenido de la pantalla splash
        ttk.Label(splash, text="Monitor del Sistema", 
                 font=("Segoe UI", 16, "bold")).pack(pady=30)
        
        # Barra de progreso indeterminada
        self.progress = ttk.Progressbar(splash, mode='indeterminate')
        self.progress.pack(pady=10, padx=50, fill='x')
        self.progress.start(10)  # Iniciar animación
        
        # Label de estado
        self.status_label = ttk.Label(splash, text="Iniciando aplicación...")
        self.status_label.pack(pady=10)
        
        # Guardar referencia al splash
        self.splash = splash
        
        # Programar el cierre del splash después de 3 segundos
        self.ventana.after(3000, self.cerrar_splash)
    
    def cerrar_splash(self):
        """Cerrar la pantalla de carga"""
        if hasattr(self, 'splash'):
            self.splash.destroy()
    
    def inicializar_background(self):
        """Inicializar componentes pesados en segundo plano"""
        try:
            # Actualizar estado: cargando información del sistema
            self.ventana.after(0, lambda: self.status_label.config(text="Cargando información del sistema..."))
            obtener_info_sistema()
            
            # Actualizar estado: cargando procesos
            self.ventana.after(0, lambda: self.status_label.config(text="Cargando procesos..."))
            obtener_procesos_optimizado()
            
            # Actualizar estado: configurando gráficas
            self.ventana.after(0, lambda: self.status_label.config(text="Configurando gráficas..."))
            
            # Finalizado
            self.ventana.after(0, lambda: self.status_label.config(text="¡Listo!"))
        except Exception as e:
            print(f"Error en inicialización: {e}")

# --- FUNCIÓN PRINCIPAL ---
def main():
    """Función principal con manejo robusto de errores"""
    try:
        # Crear e inicializar la aplicación
        app = MonitorSistema()
        app.ejecutar()
    except KeyboardInterrupt:
        # Manejo de interrupción por teclado (Ctrl+C)
        print("Aplicación cerrada por el usuario")
    except Exception as e:
        # Manejo de errores fatales
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()  # Imprimir stack trace completo

# Punto de entrada del programa
if __name__ == "__main__":
    main()