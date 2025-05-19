import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import psutil
import platform
import cpuinfo
import GPUtil
import socket
import shutil
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import threading
import sv_ttk
import matplotlib
import os
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor
import queue


def recurso_ruta(rel_path):
    """Devuelve la ruta absoluta al recurso, sea compilado o no"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# Configurar matplotlib cache
if hasattr(sys, "_MEIPASS"):
    cache_path = recurso_ruta("matplotlib_cache")
    os.environ["MPLCONFIGDIR"] = cache_path
else:
    os.environ["MPLCONFIGDIR"] = os.path.abspath("./matplotlib_cache")

# Cache global para procesos
proceso_cache = {
    'data': [],
    'last_update': 0,
    'cache_duration': 2.0  # Cache por 2 segundos
}

# Cola para comunicación entre hilos
update_queue = queue.Queue()

# --- CONFIGURACION GRAFICA ---
grafico_config = {
    "cpu_color": "#00ff00",
    "ram_color": "#ff6600",
    "disco_color": "#0099ff",
    "red_color": "#ff0066",
    "estilo": "line"
}

graficas_act = {}

# --- FUNCIONES OPTIMIZADAS ---
def obtener_info_sistema():
    """Obtiene información del sistema de forma optimizada"""
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
    """Obtiene lista de procesos de forma optimizada con cache"""
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
        print(f"Error obteniendo procesos: {e}")
        return []

def buscar_procesos_avanzada(procesos, filtro):
    """Búsqueda avanzada de procesos con regex y múltiples criterios"""
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
    """Evalúa condiciones para filtros numéricos"""
    if operador == '>':
        return valor > referencia
    elif operador == '<':
        return valor < referencia
    elif operador == '>=':
        return valor >= referencia
    elif operador == '<=':
        return valor <= referencia
    return False

class MonitorSistema:
    def __init__(self):
        self.ventana = tk.Tk()
        self.configurar_ventana()
        self.cargar_iconos()
        self.crear_interfaz()
        self.iniciar_actualizaciones()
    
    def configurar_ventana(self):
        """Configuración inicial de la ventana"""
        self.ventana.title("LeoG")
        self.ventana.geometry("1250x950")
        self.ventana.minsize(800, 600)
        sv_ttk.set_theme("dark")
        
        # Configurar el icono si existe
        try:
            self.ventana.iconbitmap(recurso_ruta("assets/dvi_leon.ico"))
        except:
            pass
    
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
    
    def crear_tab_sistema(self):
        """Crear pestaña de información del sistema"""
        self.tab_sistema = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("sistema"):
            self.notebook.add(self.tab_sistema, text=' Sistema', 
                             image=self.iconos.get("sistema"), compound="left")
        else:
            self.notebook.add(self.tab_sistema, text=' Sistema')
        
        # Frame principal con scroll
        main_frame = ttk.Frame(self.tab_sistema)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Botón de actualizar
        ttk.Button(main_frame, text="Actualizar información", 
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
        loading_label = ttk.Label(self.frame_info, text="Obteniendo información del sistema...")
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
                ttk.Label(self.frame_info, text="Interfaces de red:", 
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
                
                ttk.Label(item_frame, text=f"{clave}:", 
                         font=("Segoe UI", 10, "bold")).pack(side='left')
                ttk.Label(item_frame, text=str(valor)).pack(side='left', padx=(10, 0))
                fila += 1
    
    def crear_tab_procesos(self):
        """Crear pestaña de procesos optimizada"""
        self.tab_procesos = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("procesos"):
            self.notebook.add(self.tab_procesos, text=' Procesos', 
                             image=self.iconos.get("procesos"), compound="left")
        else:
            self.notebook.add(self.tab_procesos, text=' Procesos')
        
        # Frame de búsqueda mejorado
        frame_busqueda = ttk.Frame(self.tab_procesos)
        frame_busqueda.pack(fill='x', padx=10, pady=5)
        
        # Campo de búsqueda con ayuda
        busqueda_frame = ttk.LabelFrame(frame_busqueda, text="Búsqueda avanzada", padding=5)
        busqueda_frame.pack(fill='x')
        
        # Entry de búsqueda
        self.entrada_busqueda = ttk.Entry(busqueda_frame, font=("Segoe UI", 10))
        self.entrada_busqueda.pack(fill='x', pady=2)
        self.entrada_busqueda.bind("<KeyRelease>", self.on_search_change)
        self.entrada_busqueda.bind("<FocusIn>", self.show_search_help)
        
        # Label de ayuda
        self.help_label = ttk.Label(busqueda_frame, 
                                   text="💡 Ejemplos: 'chrome', 'cpu>50', 'ram<10', PID numérico", 
                                   font=("Segoe UI", 8), foreground="gray")
        self.help_label.pack(anchor='w')
        
        # Controles adicionales
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
        
        # Tabla de procesos
        cols = ("PID", "Nombre", "CPU %", "RAM %", "Hilos")
        self.tree = ttk.Treeview(self.tab_procesos, columns=cols, show='headings', height=25)
        
        # Configurar columnas
        anchos = {"PID": 80, "Nombre": 300, "CPU %": 100, "RAM %": 100, "Hilos": 80}
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
        self.menu_contextual.add_command(label="Terminar proceso", command=self.terminar_proceso)
        self.menu_contextual.add_command(label="Copiar PID", command=self.copiar_pid)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Información detallada", command=self.info_proceso)
        
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
        
        if messagebox.askyesno("Confirmar", f"¿Terminar proceso {nombre} (PID: {pid})?"):
            try:
                proceso = psutil.Process(int(pid))
                proceso.terminate()
                messagebox.showinfo("Éxito", f"Proceso {nombre} terminado")
                self.actualizar_tabla_procesos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo terminar el proceso: {e}")
    
    def copiar_pid(self):
        """Copiar PID al portapapeles"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = self.tree.item(item, 'values')[0]
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(pid)
        messagebox.showinfo("Copiado", f"PID {pid} copiado al portapapeles")
    
    def info_proceso(self):
        """Mostrar información detallada del proceso"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pid = int(self.tree.item(item, 'values')[0])
        
        try:
            proceso = psutil.Process(pid)
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
        """Ordenar treeview por columna"""
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
        self.info_resultados.config(text=f"Mostrando {mostrados} de {total} procesos")
    
    def crear_tab_graficas(self):
        """Crear pestaña de gráficas optimizada"""
        self.tab_graficas = ttk.Frame(self.notebook)
        
        # Agregar pestaña con o sin icono
        if self.iconos.get("graficas"):
            self.notebook.add(self.tab_graficas, text=' Gráficas', 
                             image=self.iconos.get("graficas"), compound="left")
        else:
            self.notebook.add(self.tab_graficas, text=' Gráficas')
        
        # Contenedor principal
        contenedor_paneles = ttk.Frame(self.tab_graficas)
        contenedor_paneles.pack(fill='both', expand=True, padx=10, pady=10)
        contenedor_paneles.columnconfigure((0, 1), weight=1)
        contenedor_paneles.rowconfigure((0, 1), weight=1)
        
        # Crear paneles
        self.panel_cpu = ttk.LabelFrame(contenedor_paneles, text="CPU", padding=5)
        self.panel_cpu.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.panel_ram = ttk.LabelFrame(contenedor_paneles, text="RAM", padding=5)
        self.panel_ram.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.panel_disco = ttk.LabelFrame(contenedor_paneles, text="Disco", padding=5)
        self.panel_disco.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.panel_red = ttk.LabelFrame(contenedor_paneles, text="Red", padding=5)
        self.panel_red.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Crear gráficas
        self.crear_grafica(self.panel_cpu, "CPU", psutil.cpu_percent, "cpu")
        self.crear_grafica(self.panel_ram, "RAM", lambda: psutil.virtual_memory().percent, "ram")
        self.crear_grafica(self.panel_disco, "Disco", lambda: psutil.disk_usage('/').percent, "disco")
        self.crear_grafica(self.panel_red, "Red (MB/s)", self.get_network_speed, "red")
        
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
        """Crear gráfica optimizada"""
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
                ax.set_title(f"{nombre} - Actual: {nuevo_dato:.1f}%", 
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
            self.notebook.add(self.tab_config, text=' Configuración', 
                             image=self.iconos.get("config"), compound="left")
        else:
            self.notebook.add(self.tab_config, text=' Configuración')
        
        # Frame principal
        main_frame = ttk.Frame(self.tab_config, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Configuración de gráficas
        graficas_frame = ttk.LabelFrame(main_frame, text="Configuración de gráficas", padding=10)
        graficas_frame.pack(fill="x", pady=10)
        
        # Estilo de gráfica
        self.estilo_var = tk.StringVar(value=grafico_config["estilo"])
        ttk.Label(graficas_frame, text="Estilo de gráfica:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        estilo_frame = ttk.Frame(graficas_frame)
        estilo_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(estilo_frame, text="Línea", variable=self.estilo_var, 
                       value="line", command=self.cambiar_estilo).pack(side='left', padx=10)
        ttk.Radiobutton(estilo_frame, text="Barras", variable=self.estilo_var, 
                       value="bar", command=self.cambiar_estilo).pack(side='left', padx=10)
        
        # Colores de gráficas
        colores_frame = ttk.LabelFrame(main_frame, text="Colores de gráficas", padding=10)
        colores_frame.pack(fill="x", pady=10)
        
        graficas_colores = [
            ("cpu", "CPU", self.iconos.get("cpu")),
            ("ram", "RAM", self.iconos.get("ram")),
            ("disco", "Disco", self.iconos.get("disco")),
            ("red", "Red", self.iconos.get("red"))
        ]
        
        for graf, nombre, icono in graficas_colores:
            frame = ttk.Frame(colores_frame)
            frame.pack(fill='x', pady=2)
            
            # Botón con o sin icono
            if icono:
                ttk.Button(frame, text=f"Color {nombre}", image=icono, compound="left",
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            else:
                ttk.Button(frame, text=f"Color {nombre}",
                          command=lambda g=graf: self.elegir_color(g)).pack(side='left')
            
            # Mostrar color actual
            color_actual = tk.Frame(frame, bg=grafico_config[f"{graf}_color"], 
                                  width=30, height=20)
            color_actual.pack(side='left', padx=10)
        
        # Configuración de rendimiento
        rendimiento_frame = ttk.LabelFrame(main_frame, text="Configuración de rendimiento", padding=10)
        rendimiento_frame.pack(fill="x", pady=10)
        
        ttk.Label(rendimiento_frame, text="Intervalo de actualización (segundos):").pack(anchor='w')
        self.intervalo_var = tk.DoubleVar(value=2.0)
        intervalo_scale = ttk.Scale(rendimiento_frame, from_=0.5, to=10.0, 
                                  variable=self.intervalo_var, orient="horizontal")
        intervalo_scale.pack(fill='x', pady=5)
        
        self.intervalo_label = ttk.Label(rendimiento_frame, text="2.0 segundos")
        self.intervalo_label.pack(anchor='w')
        
        def actualizar_intervalo_label(*args):
            valor = self.intervalo_var.get()
            self.intervalo_label.config(text=f"{valor:.1f} segundos")
            proceso_cache['cache_duration'] = valor
        
        self.intervalo_var.trace('w', actualizar_intervalo_label)
        
        # Botones de acción
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill='x', pady=20)
        
        ttk.Button(botones_frame, text="Aplicar configuración", 
                  command=self.aplicar_configuracion).pack(side='left', padx=5)
        ttk.Button(botones_frame, text="Restaurar predeterminados", 
                  command=self.restaurar_predeterminados).pack(side='left', padx=5)
        ttk.Button(botones_frame, text="Exportar configuración", 
                  command=self.exportar_configuracion).pack(side='left', padx=5)
    
    def cambiar_estilo(self):
        """Cambiar estilo de gráficas"""
        grafico_config["estilo"] = self.estilo_var.get()
        self.aplicar_configuracion()
    
    def elegir_color(self, nombre):
        """Elegir color para gráfica"""
        color = colorchooser.askcolor(title=f"Seleccionar color para {nombre.upper()}")
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
        messagebox.showinfo("Configuración", "Configuración restaurada a valores predeterminados")
    
    def exportar_configuracion(self):
        """Exportar configuración actual"""
        try:
            import json
            from tkinter import filedialog
            
            config_data = {
                "grafico_config": grafico_config,
                "intervalo_actualizacion": self.intervalo_var.get()
            }
            
            archivo = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Guardar configuración"
            )
            
            if archivo:
                with open(archivo, 'w') as f:
                    json.dump(config_data, f, indent=4)
                messagebox.showinfo("Éxito", f"Configuración guardada en {archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")
    
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
        """Mostrar pantalla de carga"""
        splash = tk.Toplevel()
        splash.title("Cargando...")
        splash.geometry("400x200")
        splash.resizable(False, False)
        splash.configure(bg='#2e2e2e')
        
        # Centrar splash
        splash.geometry("+%d+%d" % (
            (splash.winfo_screenwidth()/2 - 200),
            (splash.winfo_screenheight()/2 - 100)
        ))
        
        # Contenido del splash
        ttk.Label(splash, text="Monitor del Sistema", 
                 font=("Segoe UI", 16, "bold")).pack(pady=30)
        
        self.progress = ttk.Progressbar(splash, mode='indeterminate')
        self.progress.pack(pady=10, padx=50, fill='x')
        self.progress.start(10)
        
        self.status_label = ttk.Label(splash, text="Iniciando aplicación...")
        self.status_label.pack(pady=10)
        
        self.splash = splash
        
        # Cerrar splash después de 3 segundos
        self.ventana.after(3000, self.cerrar_splash)
    
    def cerrar_splash(self):
        """Cerrar pantalla de carga"""
        if hasattr(self, 'splash'):
            self.splash.destroy()
    
    def inicializar_background(self):
        """Inicializar componentes en background"""
        try:
            # Cargar información inicial
            self.ventana.after(0, lambda: self.status_label.config(text="Cargando información del sistema..."))
            obtener_info_sistema()
            
            self.ventana.after(0, lambda: self.status_label.config(text="Cargando procesos..."))
            obtener_procesos_optimizado()
            
            self.ventana.after(0, lambda: self.status_label.config(text="Configurando gráficas..."))
            
            self.ventana.after(0, lambda: self.status_label.config(text="¡Listo!"))
        except Exception as e:
            print(f"Error en inicialización: {e}")

# Función principal optimizada
def main():
    """Función principal con manejo de errores"""
    try:
        app = MonitorSistema()
        app.ejecutar()
    except KeyboardInterrupt:
        print("Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
