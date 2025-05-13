import tkinter as tk
from tkinter import ttk, colorchooser
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
import matplotlib.pyplot as plt


def recurso_ruta(rel_path):
    """Devuelve la ruta absoluta al recurso, sea compilado o no"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# 🛠 Establecer la caché de matplotlib antes de importar pyplot
if hasattr(sys, "_MEIPASS"):
    cache_path = recurso_ruta("matplotlib_cache")
    os.environ["MPLCONFIGDIR"] = cache_path  # ← aquí está el cambio
else:
    os.environ["MPLCONFIGDIR"] = os.path.abspath("./matplotlib_cache")


# --- CONFIGURACION GRAFICA ---
grafico_config = {
    "cpu_color": "#00ff00",
    "ram_color": "#ff6600",
    "disco_color": "#0099ff",
    "red_color": "#ff0066",
    "estilo": "line"
}

# Diccionario para actualizar gráficas dinámicamente
graficas_act = {}

# --- FUNCIONES ---
def obtener_info_sistema():
    uname = platform.uname()
    cpu = cpuinfo.get_cpu_info()['brand_raw']
    memoria = psutil.virtual_memory()
    disco_total, _, _ = shutil.disk_usage("/")
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    interfaces = psutil.net_if_addrs()
    red = {}
    for interfaz, direcciones in interfaces.items():
        for dir in direcciones:
            if dir.family == socket.AF_INET:
                red[interfaz] = dir.address
    gpus = GPUtil.getGPUs()
    gpu_info = gpus[0].name if gpus else "No detectada"
    return {
        "Sistema operativo": uname.system,
        "Nombre del equipo": uname.node,
        "Versión": uname.version,
        "Arquitectura": uname.machine,
        "Procesador": cpu,
        "RAM total": f"{round(memoria.total / (1024**3), 2)} GB",
        "Disco total": f"{round(disco_total / (1024**3), 2)} GB",
        "GPU": gpu_info,
        "Uptime": str(uptime).split('.')[0],
        "Red": red,
    }

def actualizar_tabla_procesos(tree):
    for row in tree.get_children():
        tree.delete(row)
    procesos = [(p.info['pid'], p.info['name'], p.info['cpu_percent'], p.info['memory_percent'], p.num_threads())
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]
    for proc in sorted(procesos, key=lambda x: x[2], reverse=True):
        tree.insert('', tk.END, values=proc)

def crear_grafica(frame, nombre, y_data, color_key):
    fig, ax = plt.subplots(figsize=(4.5, 2.5), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(padx=10, pady=10, fill="both", expand=True)
    x = list(range(60))
    datos = [0]*60

    def actualizar():
        datos.pop(0)
        datos.append(y_data())
        ax.clear()
        color = grafico_config[color_key + "_color"]
        estilo = grafico_config["estilo"]
        if estilo == "line":
            ax.plot(x, datos, label=nombre, color=color, linewidth=2)
        else:
            ax.bar(x, datos, color=color, width=0.8)
        ax.set_ylim(0, max(100, max(datos)*1.2))
        ax.set_title(f"{nombre} (%)", color='white', fontsize=10)
        ax.set_facecolor('#2e2e2e')
        fig.patch.set_facecolor('#2e2e2e')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        canvas.draw()
        frame.after(1000, actualizar)

    actualizar()
    graficas_act[color_key] = actualizar

# --- INTERFAZ PRINCIPAL ---
ventana = tk.Tk()

# --- CARGA DE ICONOS ---
iconos = {
    "sistema": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/system.png")).resize((20, 20))),
    "procesos": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/processes.png")).resize((20, 20))),
    "graficas": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/chart.png")).resize((20, 20))),
    "config": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/config.png")).resize((20, 20))),
    "cpu": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/cpu.png")).resize((16, 16))),
    "ram": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/ram.png")).resize((16, 16))),
    "disco": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/disk.png")).resize((16, 16))),
    "red": ImageTk.PhotoImage(Image.open(recurso_ruta("assets/network.png")).resize((16, 16))),
}

ventana.iconbitmap(recurso_ruta("assets/dvi_leon.ico"))

ventana.title("Monitor del Sistema")
ventana.geometry("1250x950")
sv_ttk.set_theme("dark")

notebook = ttk.Notebook(ventana)
notebook.pack(fill='both', expand=True)

# --- PESTAÑA SISTEMA ---
tab_sistema = ttk.Frame(notebook)
notebook.add(tab_sistema, text=' Sistema', image=iconos["sistema"], compound="left")
info = obtener_info_sistema()
frame_sistema = ttk.Frame(tab_sistema, padding=20)
frame_sistema.pack(fill="both", expand=True)
fila = 0
for clave, valor in info.items():
    if clave == "Red":
        ttk.Label(frame_sistema, text="Interfaces de red:", font=("Segoe UI", 12, "bold")).grid(column=0, row=fila, sticky='w')
        fila += 1
        for interfaz, ip in valor.items():
            ttk.Label(frame_sistema, text=f"{interfaz}: {ip}").grid(column=0, row=fila, sticky='w')
            fila += 1
    else:
        ttk.Label(frame_sistema, text=f"{clave}: {valor}").grid(column=0, row=fila, sticky='w')
        fila += 1

# --- PESTAÑA PROCESOS ---
tab_procesos = ttk.Frame(notebook)
notebook.add(tab_procesos, text=' Procesos', image=iconos["procesos"], compound="left")
cols = ("PID", "Nombre", "CPU %", "RAM %", "Hilos")

# Campo de búsqueda
frame_busqueda = ttk.Frame(tab_procesos)
frame_busqueda.pack(fill='x', padx=10, pady=5)
ttk.Label(frame_busqueda, text="Buscar proceso:").pack(side='left')
entrada_busqueda = ttk.Entry(frame_busqueda)
entrada_busqueda.pack(side='left', fill='x', expand=True, padx=5)

tree = ttk.Treeview(tab_procesos, columns=cols, show='headings', height=25)
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=200)
tree.pack(fill="both", expand=True, padx=10, pady=10)

# Función para filtrar
def actualizar_tabla_procesos_filtrada():
    filtro = entrada_busqueda.get().lower()
    for row in tree.get_children():
        tree.delete(row)
    procesos = [(p.info['pid'], p.info['name'], p.info['cpu_percent'], p.info['memory_percent'], p.num_threads())
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]
    for proc in sorted(procesos, key=lambda x: x[2], reverse=True):
        if filtro in str(proc[1]).lower():
            tree.insert('', tk.END, values=proc)

entrada_busqueda.bind("<KeyRelease>", lambda e: actualizar_tabla_procesos_filtrada())

# Reemplaza la función de actualización periódica
def actualizar_periodicamente():
    actualizar_tabla_procesos_filtrada()
    ventana.after(5000, actualizar_periodicamente)

actualizar_tabla_procesos_filtrada()
actualizar_periodicamente()

def actualizar_periodicamente():
    actualizar_tabla_procesos(tree)
    ventana.after(5000, actualizar_periodicamente)
actualizar_periodicamente()

# --- PESTAÑA GRAFICAS ---
tab_graficas = ttk.Frame(notebook)
notebook.add(tab_graficas, text=' Gráficas', image=iconos["graficas"], compound="left")
contenedor_paneles = ttk.Frame(tab_graficas)
contenedor_paneles.pack(fill='both', expand=True)
contenedor_paneles.columnconfigure((0, 1), weight=1)
contenedor_paneles.rowconfigure((0, 1), weight=1)

panel_cpu = ttk.Frame(contenedor_paneles, relief="groove")
panel_cpu.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
panel_ram = ttk.Frame(contenedor_paneles, relief="groove")
panel_ram.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
panel_disco = ttk.Frame(contenedor_paneles, relief="groove")
panel_disco.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
panel_red = ttk.Frame(contenedor_paneles, relief="groove")
panel_red.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

crear_grafica(panel_cpu, "CPU", psutil.cpu_percent, "cpu")
crear_grafica(panel_ram, "RAM", lambda: psutil.virtual_memory().percent, "ram")
crear_grafica(panel_disco, "Disco", lambda: psutil.disk_usage('/').percent, "disco")
crear_grafica(panel_red, "Red (MB enviados)", lambda: psutil.net_io_counters().bytes_sent / (1024*1024), "red")

# --- PERSONALIZACION ---
def elegir_color(nombre):
    color = colorchooser.askcolor()[1]
    if color:
        grafico_config[nombre + "_color"] = color

def cambiar_estilo():
    grafico_config["estilo"] = estilo_var.get()

# Forzar redibujado inmediato
def aplicar_configuracion():
    for clave, funcion in graficas_act.items():
        funcion()

# Interfaz personalización
tab_config = ttk.Frame(notebook)
notebook.add(tab_config, text=' Configuración', image=iconos["config"], compound="left")
estilo_var = tk.StringVar(value=grafico_config["estilo"])
ttk.Label(tab_config, text="Estilo de gráfica:").pack(pady=5)
ttk.Radiobutton(tab_config, text="Línea", variable=estilo_var, value="line", command=lambda: [cambiar_estilo(), aplicar_configuracion()]).pack()
ttk.Radiobutton(tab_config, text="Barras", variable=estilo_var, value="bar", command=lambda: [cambiar_estilo(), aplicar_configuracion()]).pack()

for graf in ["cpu", "ram", "disco", "red"]:
    ttk.Button(
        tab_config,
        text=f" Color {graf.upper()}",
        image=iconos[graf],
        compound="left",
        command=lambda g=graf: [elegir_color(g), aplicar_configuracion()]
    ).pack(pady=2)

ventana.mainloop()


