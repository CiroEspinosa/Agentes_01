# Proyecto de Agentes Distribuidos

Este proyecto implementa un sistema distribuido basado en **agentes RACI** que interactúan entre sí utilizando microservicios. El sistema está diseñado para la generación, procesamiento y distribución de archivos, gestionado por **FastAPI** en el backend y **Streamlit** en el frontend.

## Agentes RACI

- **User Proxy**: El agente con el que interactúa el usuario.
- **Assistant**: Agente principal que coordina las solicitudes.
- **Agentes especializados**: Realizan tareas específicas como la generación de archivos en PDF y Excel.

## ¿Qué hace actualmente?

- Comunicación entre microservicios usando **Kafka** y **Zookeeper**.
- Generación automática y procesamiento de archivos.
- Interfaz de usuario en **Streamlit**.
- Backend con **FastAPI**.

## Tecnologías

- **Python**
- **FastAPI**
- **Streamlit**
- **Docker**
- **Kafka**, **Zookeeper**

## Instalación

1. Clona el repositorio:

   ```bash
   git clone <URL del repositorio>
   cd <nombre del proyecto>
