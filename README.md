🖥️ Leo-G 🦁

Monitor del Sistema / System Monitor

🇪🇸 Español

📋 Descripción

Leo-G es una aplicación de escritorio desarrollada en Python que da información detallada sobre el rendimiento y estado de tu sistema en tiempo real. Con una interfaz gráfica elegante y optimizada, permite monitorear CPU, RAM, disco, red y procesos del sistema.

✨ Características

Información del Sistema: Muestra detalles completos del hardware y software

Monitor de Procesos: Lista y gestiona procesos en tiempo real con búsqueda avanzada

Gráficas en Tiempo Real: Visualización dinámica del uso de CPU, RAM, disco y red

Configuración Personalizable: Colores y estilos de gráfica configurables

Búsqueda Avanzada: Filtros por nombre, PID, uso de CPU/RAM con soporte para regex

Interfaz Oscura: Tema oscuro para mayor comodidad visual

Optimizado: Cache inteligente y actualizaciones eficientes


🌐 Sitio Web

Portal Web: Plataforma informativa con documentación completa
![image](https://github.com/user-attachments/assets/fdae430f-84e0-485c-b03e-90946e7b7532)


Sección de Características: Detalles visuales de todas las funcionalidades
![image](https://github.com/user-attachments/assets/70b5d9f7-a71f-43d4-9d50-891a917327ff)

Guía de Descarga: Instrucciones paso a paso para diferentes sistemas operativos
![image](https://github.com/user-attachments/assets/accbeade-2bff-4089-80a2-54e966e2ea73)

Formulario de Contacto: Canal directo para feedback, sugerencias y reporte de bugs
![image](https://github.com/user-attachments/assets/e58e4c69-1fc8-4257-b9ab-1e357f236a2f)

Roadmap Público: Próximas actualizaciones y características en desarrollo
![image](https://github.com/user-attachments/assets/f2253c18-201e-4cf5-acdd-482dbf6bb612)

Software Libre: Código 100% abierto con licencia GPL v3 y desarrollo comunitario

🛠️ Requisitos

Python 3.7 o superior
Librerías requeridas (ver requirements.txt):
tkinter
psutil
matplotlib
Pillow
cpuinfo
GPUtil
sv-ttk


📦 Instalación

Clonar el repositorio:
````palintext
bashgit/git clone https://github.com/Miguel01923/TFG
`````
````palitext
cd monitor-sistema
````
Instalar dependencias:

`````palitext
bashpip install -r requirements.txt
``````

Ejecutar la aplicación:

`````palitext
bashpython monitor_sistema.py
``````

🚀 Uso

Pestaña Sistema

![image](https://github.com/user-attachments/assets/aac8d166-88a8-4c78-8e25-edd044e60de0)

Muestra información completa del hardware
Detalles del procesador, memoria, almacenamiento y red
Información del sistema operativo y tiempo de actividad

Pestaña Procesos

![image](https://github.com/user-attachments/assets/6de54274-5a0e-4042-833a-fe51f985dce6)

Lista todos los procesos activos
Búsqueda avanzada:

![image](https://github.com/user-attachments/assets/7be45d43-ebb7-4e7c-a803-d6465dae7d7b)

Por nombre: chrome, firefox
Por PID: 1234
Por uso de CPU: cpu>50 (mayor a 50%)
Por uso de RAM: ram<10 (menor a 10%)
Soporte regex: .*python.*


Menú contextual para terminar procesos y ver detalles
Ordenamiento por cualquier columna

Pestaña Gráficas

![image](https://github.com/user-attachments/assets/834231d4-ba4d-4153-ae99-9fa15883a533)

Monitoreo en tiempo real de:

Uso de CPU (%)
Uso de RAM (%)
Uso de disco (%)
Velocidad de red (MB/s)


Gráficas actualizadas cada segundo

Pestaña Configuración

![image](https://github.com/user-attachments/assets/f47cd28d-37bf-4107-98a0-1cb0953f6c60)

Personalizar colores de las gráficas
Cambiar entre estilos de línea y barras
Ajustar intervalo de actualización
Exportar/importar configuración

Pestaña Grabación

![image](https://github.com/user-attachments/assets/56c98e5f-8cac-4bc0-a4a4-15ecc02761fc)

Permite graabar el funcionamiento y devolverte un pdf con las mediciones 


🔧 Características Técnicas

Cache Inteligente: Los procesos se cachean por 2 segundos para mejor rendimiento
Actualizaciones Optimizadas: Solo se actualizan los datos necesarios
Manejo de Errores: Captura y maneja errores graciosamente
Threading: Operaciones pesadas en hilos separados
Interfaz Responsiva: Se adapta a diferentes tamaños de ventana

📁 Estructura del Proyecto

````palintext
Leo-G/
├── .vscode/
│   └── settings.json
├── assets/
│   ├── chart.png
│   ├── config.png
│   ├── cpu.png
│   ├── disk.png
│   ├── dvi_leon.ico
│   ├── processes.png
│   ├── network.png
│   ├── ram.png
│   └── system.png
├── web_Leo-G/
│   ├── .vscode/
│   │   └── settings.json
│   ├── img/
│   │   ├── color.png
│   │   ├── demo.1.png
│   │   ├── descargapdf.png
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── logo_400x400_white_bg.jpg
│   │   ├── logo.4.png
│   │   ├── sistema.png
│   │   └── sistemaejemplo.png
│   ├── caracteristicas.html
│   ├── contacto.html
│   ├── descarga.html
│   ├── index.html
│   └── rodemap.html
├── Leo-G_comentado.py
├── Leo-G.py
└── requirements.txt
````
🎯 Compilación a Ejecutable

Para crear un ejecutable independiente:
````palintext
bashpip install pyinstaller
````

````palintext
pyinstaller --onefile --windowed --add-data "assets;assets" monitor_sistema.py
````


🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

Fork TFG

Crea una rama para tu feature 
````falintext
(git checkout -b feature/nueva-caracteristica)
````
Commit tus cambios 

````falintext
(git commit -am 'Agrega nueva característica')
````
Push a la rama 
````falintext
(git push origin feature/nueva-caracteristica)
````
Abre un Pull Request desde tu repositorio forkeado hacia el repositorio original.

¡Muchas gracias por contribuir! No olvides describir claramente tu cambio en el Pull Request.😉


🐛 Reportar Problemas

Si encuentras algún problema, por favor abre un issue con:

Descripción del problema

Pasos para reproducirlo

Sistema operativo y versión de Python

Logs de error si están disponibles



🇺🇸 English

📋 Description

Leo-G is a desktop application developed in Python that provides detailed information about your system's performance and status in real-time. With a modern and optimized graphical interface, it allows monitoring CPU, RAM, disk, network, and system processes.

✨ Features

System Information: Shows complete hardware and software details

Process Monitor: Lists and manages processes in real-time with advanced search

Real-Time Graphics: Dynamic visualization of CPU, RAM, disk, and network usage

Customizable Configuration: Configurable chart colors and styles

Advanced Search: Filters by name, PID, CPU/RAM usage with regex support

Dark Interface: Dark theme for better visual comfort

Optimized: Smart caching and efficient updates

🌐 Website

Web Portal: Informative platform with complete documentation
![image](https://github.com/user-attachments/assets/fdae430f-84e0-485c-b03e-90946e7b7532)

Features Section: Visual details of all functionalities
![image](https://github.com/user-attachments/assets/70b5d9f7-a71f-43d4-9d50-891a917327ff)

Download Guide: Step-by-step instructions for different operating systems
![image](https://github.com/user-attachments/assets/accbeade-2bff-4089-80a2-54e966e2ea73)

Contact Form: Direct channel for feedback, suggestions, and bug reporting
![image](https://github.com/user-attachments/assets/e58e4c69-1fc8-4257-b9ab-1e357f236a2f)

Public Roadmap: Upcoming updates and features in development
![image](https://github.com/user-attachments/assets/f2253c18-201e-4cf5-acdd-482dbf6bb612)

Free Software: 100% open source code with GPL v3 license and community development


🛠️ Requirements

Python 3.7 or higher

Required libraries (see requirements.txt):

tkinter

psutil

matplotlib

Pillow

cpuinfo

GPUtil

sv-ttk


📦 Installation

Clone the repository:
````palintext
bashgit clone https://github.com/your-user/system-monitor.git
````
`````palintext
cd system-monitor
``````

Install dependencies:
`````palintext
bashpip install -r requirements.txt
`````

Run the application:
````palintext
bashpython monitor_sistema.py
````

🚀 Usage

System Tab
![image](https://github.com/user-attachments/assets/eadddd1c-328c-4974-a22e-6d7f4bb541ba)


Shows complete hardware information
Processor, memory, storage, and network details
Operating system information and uptime

Processes Tab
![image](https://github.com/user-attachments/assets/82256fe3-5310-4077-93f2-bd71a342783d)


Lists all active processes
Advanced search:
![image](https://github.com/user-attachments/assets/2fe15417-6b33-4b7d-b27b-3271e31ed64c)

By name: chrome, firefox
By PID: 1234
By CPU usage: cpu>50 (greater than 50%)
By RAM usage: ram<10 (less than 10%)
Regex support: .*python.*


Context menu to terminate processes and view details
Sorting by any column

Charts Tab
![image](https://github.com/user-attachments/assets/4e2e0a32-e0cc-40d9-b05e-7793dfe5c532)

Real-time monitoring of:

CPU usage (%)
RAM usage (%)
Disk usage (%)
Network speed (MB/s)


Charts updated every second

Configuration Tab
![image](https://github.com/user-attachments/assets/0fc5984c-8a07-4b6d-8718-eeb2540425c4)

Customize chart colors
Switch between line and bar styles
Adjust update interval
Export/import configuration

Recording Tab
![image](https://github.com/user-attachments/assets/85531d0c-5476-41cd-b93a-029d29e9d3c0)

Allows recording of the operation and returns a PDF with the measurements.

🔧 Technical Features

Smart Caching: Processes are cached for 2 seconds for better performance
Optimized Updates: Only necessary data is updated
Error Handling: Gracefully captures and handles errors
Threading: Heavy operations in separate threads
Responsive Interface: Adapts to different window sizes

📁 Project Structure
```plaitext
Leo-G/
├── .vscode/
│   └── settings.json
├── assets/
│   ├── chart.png
│   ├── config.png
│   ├── cpu.png
│   ├── disk.png
│   ├── dvi_leon.ico
│   ├── processes.png
│   ├── network.png
│   ├── ram.png
│   └── system.png
├── web_Leo-G/
│   ├── .vscode/
│   │   └── settings.json
│   ├── img/
│   │   ├── color.png
│   │   ├── demo.1.png
│   │   ├── descargapdf.png
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── logo_400x400_white_bg.jpg
│   │   ├── logo.4.png
│   │   ├── sistema.png
│   │   └── sistemaejemplo.png
│   ├── caracteristicas.html
│   ├── contacto.html
│   ├── descarga.html
│   ├── index.html
│   └── rodemap.html
├── Leo-G_comentado.py
├── Leo-G.py
└── requirements.txt
```
🎯 Building to Executable

To create a standalone executable:
`````palintext
bash pip install pyinstaller
``````
`````palintext
pyinstaller --onefile --windowed --add-data "assets;assets" monitor_sistema.py
``````

🤝 Contributing
Contributions are welcome. Please:

Fork the project

Create a feature branch 
````palintext
(git checkout -b feature/new-feature)
````
Commit your changes 
`````palintext
(git commit -am 'Add new feature')
``````
Push to the branch 
`````palintext
(git push origin feature/new-feature)
``````

Open a Pull Request from your forked repository to the original repository.

Thank you very much for contributing! Don't forget to clearly describe your change in the Pull Request.😉


🐛 Reporting Issues

If you find any problems, please open an issue with:

Problem description

Steps to reproduce

Operating system and Python version

Error logs if available



🙏 Acknowledgments / Agradecimientos

psutil - Cross-platform library for system monitoring

matplotlib - Plotting library for Python

sv-ttk - Modern dark theme for tkinter

