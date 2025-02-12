import streamlit as st
import requests
import time
import os

# URL del endpoint donde se enviará el archivo
UPLOAD_URL = "http://tool_file_reader:7121/files/upload/"
LIST_URL = "http://tool_file_reader:7121/files/list"
LIST_GEN_URL = "http://tool_file_generator:7122/files/list"
OUTPUT_FOLDER = "generated_files"

data = {
        "Herramientas (Tools)": [
            {"Nombre": "tool_closet", "Puerto": "7120"},
            {"Nombre": "tool_file_reader", "Puerto": "7121"},
            {"Nombre": "tool_file_generator", "Puerto": "7122"},
        ],
        "Agentes (Agents)": [
            {"Nombre": "stylist_planner", "Puerto": "10000"},
            {"Nombre": "clothes_provider", "Puerto": "10001"},
            {"Nombre": "clothes_user_proxy", "Puerto": "10002"},
            {"Nombre": "circus_user_proxy", "Puerto": "10003"},
            {"Nombre": "joker_agent", "Puerto": "10004"},
            {"Nombre": "explainer_agent", "Puerto": "10005"},
            {"Nombre": "file_user_proxy", "Puerto": "10006"},
            {"Nombre": "file_reader", "Puerto": "10007"},
            {"Nombre": "file_assistant", "Puerto": "10008"},
        ],
        "Users proxy": [ 
            {"Nombre": "clothes_user_proxy", "Puerto": "10002"},
            {"Nombre": "circus_user_proxy", "Puerto": "10003"},
            {"Nombre": "file_user_proxy", "Puerto": "10006"},
        ],
        "Swarms": [
            {"Nombre": "stylist_swarm", "Puerto": "10100"},
            {"Nombre": "circus_swarm", "Puerto": "10101"},
            {"Nombre": "file_swarm", "Puerto": "10102"},
        ],
        "Frontend (Streamlit)": [
            {"Nombre": "streamlit_frontend", "Puerto": "8501"},
        ],
    }

# Configuración inicial dinámica
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://file_user_proxy:10006"
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = "user"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "respuesta_completada" not in st.session_state:
    st.session_state.respuesta_completada = False

st.set_page_config(layout="wide")

# Sidebar para subir archivos y mostrar información relevante
with st.sidebar:
    st.title("Opciones")
    st.subheader("Subir archivo")
    uploaded_file = st.file_uploader("Elige un archivo")

    
    if uploaded_file is not None:
        st.write(f"Archivo seleccionado: {uploaded_file.name}")
        if st.button("Subir archivo"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            headers = {"Content-Type": "multipart/form-data"}
            try:
                response = requests.post(UPLOAD_URL, files=files)
                if response.status_code == 200:
                    st.success("Archivo subido con éxito.")
                else:
                    st.error(f"Error al subir el archivo: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error de conexión: {e}")
    
    st.subheader("Archivos generados")          

    if st.button("Actualizar lista de archivos generados"):
        try:
            response = requests.get(LIST_GEN_URL)
            if response.status_code == 200:
                file_list = response.json().get("files", [])  # Extraer la lista de archivos
                if file_list:
                    st.write("Archivos disponibles:")
                    for file in file_list:
                        filename = file.get("filename", "Desconocido")
                        download_url = file.get("download_url", "#")
                        # Mostrar el nombre del archivo con un enlace de descarga
                        st.markdown(f"- [{filename}]({download_url})")
                else:
                    st.info("No hay archivos disponibles.")
            else:
                st.error(f"Error al obtener la lista de archivos: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")

    st.subheader("Archivos subidos")          

    if st.button("Actualizar lista de archivos"):
        try:
            response = requests.get(LIST_URL)
            if response.status_code == 200:
                file_list = response.json().get("files", [])  # Extraer la lista de archivos
                if file_list:
                    st.write("Archivos disponibles:")
                    for file in file_list:
                        st.write(f"- {file}")
                else:
                    st.info("No hay archivos disponibles.")
            else:
                st.error(f"Error al obtener la lista de archivos: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")

    st.subheader("Información de Herramientas, Agentes y Swarms")

    # Mostrar datos en expansores para ahorrar espacio
    for category, items in data.items():
        with st.expander(category):
            for item in items:
                st.write(f"**{item['Nombre']}**: Puerto `{item['Puerto']}`")

###############################################################################
#                       Funciones auxiliares del backend                      #
###############################################################################
def start_conversation(swarm: str, user: str, request: str):
    """Inicia una conversación con el backend."""
    url = f"{ st.session_state.api_base_url}/conversation"
    payload = {"swarm": swarm, "user": user, "request": request}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        conversation_data = response.json()
        conversation_id = conversation_data["header"]["conversation_id"]
        return {
            "conversation_id": conversation_id,
            "messages": conversation_data["messages"]
        }
    else:
        st.error(f"Error al iniciar la conversación: {response.text}")
        return None

def get_conversation_status(user: str, conversation_id: str):
    """Obtiene todo el historial de la conversación desde el backend."""
    url = f"{st.session_state.api_base_url}/conversation/{user}/{conversation_id}"
    response = requests.get(url)
    if response.status_code == 200:
        conversation_data = response.json()
        return conversation_data["messages"]
    else:
        st.error(f"Error al recuperar el historial: {response.text}")
        return None

def reply_to_conversation(conversation_id: str, user_id: str, content: str):
    """Envía un nuevo mensaje a una conversación existente."""
    url = f"{st.session_state.api_base_url}/reply"
    payload = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "content": content
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()  # {"messages": [...]}
    else:
        st.error(f"Error al responder: {response.text}")
        return None

###############################################################################
#                   Lógica de espera (polling) para la respuesta              #
###############################################################################
def wait_for_pending_user_reply(user: str, conversation_id: str, initial_history_length: int, max_checks: int = 15, interval: float = 3.0):
    """
    Consulta el backend cada 'interval' segundos, hasta 'max_checks' veces,
    para ver si algún mensaje tiene pending_user_reply=True.
    Solo procesa los mensajes nuevos añadidos después del initial_history_length.
    """
    for _ in range(max_checks):
        with st.spinner("Generando la respuesta..."):
            new_messages = get_conversation_status(user, conversation_id)
            if new_messages is not None:
                # Procesar solo mensajes nuevos
                recent_messages = new_messages[initial_history_length:]
                if recent_messages:
                    existing = {(m["role"], m["content"]) for m in st.session_state.chat_history}
                    for msg in recent_messages:
                        if (msg["role"], msg["content"]) not in existing:
                            st.session_state.chat_history.append(msg)

                    # ¿Hay mensajes con pending_user_reply=True?
                    if any(m.get("pending_user_reply") for m in recent_messages):
                        st.session_state.respuesta_completada = True
                        return True

        time.sleep(interval)

    st.session_state.respuesta_completada = False
    return False

###############################################################################
#                           Interfaz principal (Chat)                         #
###############################################################################
def chat_interface():
    st.title("Agente Conversacional - Chat")
    
    # Extraer nombres de swarms y agentes
    swarms = [swarm["Nombre"] for swarm in data["Swarms"]]
    users_proxy = [user_proxy["Nombre"] for user_proxy in data["Users proxy"]]
    ports = {item["Nombre"]: item["Puerto"] for group in data.values() for item in group}

    # Interfaz de selección en Streamlit
    swarm = st.selectbox("Swarm", swarms, index=swarms.index("file_swarm"))
    api_proxy = st.selectbox("Proxy", users_proxy, index=users_proxy.index("file_user_proxy"))
    api_port = ports.get(api_proxy, "10006")
    st.session_state.api_base_url = f"http://{api_proxy}:{api_port}"

    # Entrada de usuario
    user_id = st.text_input("Usuario", value=st.session_state.get("user_id", ""))
    st.session_state.user_id = user_id

    st.divider()

    ################### MOSTRAR HISTORIAL EN FORMATO CHAT #####################
    for msg in st.session_state.chat_history:
        if msg["role"] == "system":
            continue

        role_label = msg["role"]
        if role_label == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif role_label in ["assistant", "bot"]:
            with st.chat_message("assistant"):
                st.write(msg["content"])
        else:
            with st.chat_message(role_label):
                st.write(msg["content"])

    st.divider()

    ############### CAMPO DE ENTRADA ESTILO CHAT ##############################
    user_text = st.chat_input("Escribe tu mensaje y pulsa Enter...")

    if user_text:
        # Guardar el estado inicial del historial
        initial_history_length = len(st.session_state.chat_history)

        if st.session_state.conversation_id is None:
            conversation = start_conversation(swarm, user_id, user_text)
            if conversation:
                st.session_state.conversation_id = conversation["conversation_id"]
                for m in conversation["messages"]:
                    if m not in st.session_state.chat_history:
                        st.session_state.chat_history.append(m)
        else:
            reply = reply_to_conversation(st.session_state.conversation_id, user_id, user_text)
            st.session_state.chat_history.append({"role": "user", "content": user_text})

            if reply and "messages" in reply:
                existing = {(m["role"], m["content"]) for m in st.session_state.chat_history}
                for m in reply["messages"]:
                    if (m["role"], m["content"]) not in existing:
                        st.session_state.chat_history.append(m)

        # Polling para esperar respuestas pendientes
        if st.session_state.conversation_id:
            found = wait_for_pending_user_reply(
                user=user_id, 
                conversation_id=st.session_state.conversation_id,
                initial_history_length=initial_history_length,
                max_checks=15,
                interval=3.0
            )
            if not found:
                st.info("No se recibió una respuesta final en el tiempo esperado.")

    st.divider()

    ################ BOTÓN "ACTUALIZAR CHAT" ##################################
    if st.button("Actualizar chat"):
        
        if st.session_state.conversation_id:
            updated_messages = get_conversation_status(
                user=user_id,
                conversation_id=st.session_state.conversation_id
            )
            if updated_messages:
                existing = {(m["role"], m["content"]) for m in st.session_state.chat_history}
                for msg in updated_messages:
                    if (msg["role"], msg["content"]) not in existing:
                        st.session_state.chat_history.append(msg)
            st.success("Chat actualizado correctamente.")
        else:
            st.warning("No hay conversación activa.")

    # Mostrar mensaje de respuesta completada
    if st.session_state.respuesta_completada:
        st.success("¡Completado, actualiza la conversación!")
        st.session_state.respuesta_completada = False

###############################################################################
#                           LOGS DE CONVERSACIÓN                              #
###############################################################################
def logs_interface():
    st.title("Logs de conversación")
    st.write("Aquí verás **todos** los mensajes, incluyendo todos los atributos disponibles:")
    
    # Botón para actualizar los logs
    if st.button("Actualizar logs"):
        if st.session_state.conversation_id:
            # Recuperar mensajes actualizados
            updated_messages = get_conversation_status(
                user=st.session_state.user_id,
                conversation_id=st.session_state.conversation_id
            )
            if updated_messages:
                existing = {(m["role"], m["content"]) for m in st.session_state.chat_history}
                for msg in updated_messages:
                    if (msg["role"], msg["content"]) not in existing:
                        st.session_state.chat_history.append(msg)
            st.success("Logs actualizados correctamente.")
        else:
            st.warning("No hay conversación activa para actualizar los logs.")

    # Mostrar todos los mensajes del historial en formato JSON
    for msg in st.session_state.chat_history:
        st.json(msg)

###############################################################################
#                       Render Tabs (Chat y Logs)                             #
###############################################################################
tab1, tab2 = st.tabs(["Chat", "Logs"])
with tab1:
    chat_interface()
with tab2:
    logs_interface()
