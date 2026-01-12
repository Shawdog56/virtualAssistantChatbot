# Virtual Assistant Chatbot: Desktop Interface

[![Licencia](https://img.shields.io/badge/Licencia-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blue)](https://github.com/TomSchimansky/CustomTkinter)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

Este repositorio contiene la interfaz gráfica y el motor de chatbot para el ecosistema de **Asistente Huesos**. Es una aplicación de escritorio moderna desarrollada en Python que permite al usuario ejecutar comandos, gestionar multimedia y controlar dispositivos IoT de forma intuitiva.

---

## Funcionalidades Core

El chatbot está organizado en módulos especializados para ofrecer una experiencia integral:

* **Music Player:** Módulo dedicado para la gestión y reproducción de listas de música locales o mediante integración.
* **Searcher:** Motor de búsqueda integrado para consultas rápidas y obtención de información.
* **Lister:** Sistema de gestión de tareas y visualización de estados del sistema.
* **Flash Device:** Herramienta integrada para la configuración y flasheo de microcontroladores (nodos IoT) para asegurar su correcta integración al ecosistema.

---

## Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **GUI Framework:** `CustomTkinter` (para una apariencia moderna y soporte de modo oscuro nativo).
* **Comunicación:** Integración con protocolos para interacción con el servidor central de Asistente Huesos.
* **Containerización:** Soporte completo para `Docker` y `Docker Compose` para despliegues rápidos.

---

## Estructura del Software

```text
virtualAssistantChatbot/
├── music_player/    # Control y gestión de audio
├── searcher/        # Lógica de búsquedas y consultas
├── lister/          # Gestión de listas y visualización
├── chatbot.py       # Punto de entrada principal y lógica de la GUI
└── flash_device.py  # Utilidad para configuración de hardware IoT
```

## Instalación y ejecución
git clone [https://github.com/Shawdog56/virtualAssistantChatbot.git](https://github.com/Shawdog56/virtualAssistantChatbot.git)
cd virtualAssistantChatbot
pip install -r requirements.txt
python chatbot.py
