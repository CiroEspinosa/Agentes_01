## 🔍 1. Diagnóstico de problemas (Ver qué está fallando)
```bash
sudo lsof -i :10001        # Ver qué proceso usa el puerto 10001
netstat -an | grep 7120    # Buscar conexiones activas en el puerto 7120
docker ps                 # Listar contenedores en ejecución
docker compose logs -f file_swarm  # Ver logs en tiempo real de file_swarm
```

## 🛑 2. Detener procesos problemáticos
```bash
sudo kill -9 <PID>         # Forzar cierre del proceso en conflicto
docker stop distiller_plus-file_reader_agent-1  # Detener contenedor específico
docker rm distiller_plus-file_reader_agent-1    # Eliminar contenedor detenido
docker compose down --remove-orphans  # Apagar contenedores y limpiar huérfanos
```

## 🔄 3. Reiniciar y limpiar Docker
```bash
docker system prune -f      # Limpiar contenedores, imágenes y volúmenes no usados
sudo systemctl restart docker  # Reiniciar el servicio de Docker
docker compose down         # Apagar los contenedores y redes
docker compose build        # Construir las imágenes de nuevo
docker compose up -d        # Levantar los contenedores en segundo plano
docker compose restart file_user_proxy file_generator file_reader file_assistant tool_file_reader tool_file_generator # Reiniciar contenedores
```

## 📡 4. Consultar APIs con curl
```bash
curl http://localhost:7122/openapi.json | jq .  # Obtener documentación de API
curl -X GET "http://localhost:7121/files/list"  # Listar archivos disponibles
curl -O "http://localhost:7122/files/download/text1.pdf"  # Descargar archivo
```

## 📤 5. Enviar datos a la API
```bash
curl -X POST "http://localhost:7122/files/generate/" \
-H "Content-Type: application/json" \
-d '{"type": "excel", "content": [{"col1": "value1", "col2": "value2"}]}'  
# Generar un archivo Excel

curl -X POST http://localhost:10006/conversation \
-H "Content-Type: application/json" \
-d '{"swarm": "file_swarm", "user": "user", "request": "Hola"}'
# Enviar una conversación a file_swarm

curl -X POST http://localhost:7121/files/read/ \
-H "Content-Type: multipart/form-data" \
-F "file=@/home/ciro/Project/DIPLOMA FORMACIÓN PRESENCIAL_27-01-2025_Tecnilógica.pptx"
# Subir un archivo para su lectura

 # Obtener el contenido de un archivo ya subido (/files/content/{filename})

curl -X GET "http://localhost:7121/files/content/nombre_del_archivo.txt"

curl -X POST "http://localhost:7121/files/upload/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@ruta/del/archivo.txt"

curl -X GET "http://localhost:7121/files/list"

curl -X 'POST' 'http://127.0.0.1:7121/files/upload/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/home/ciro/Project/TARJETA RESTAURANTE.pdf'
"\\wsl.localhost\Ubuntu\home\ciro\Project\TARJETA RESTAURANTE.pdf"