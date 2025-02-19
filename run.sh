#!/bin/bash

 echo "Deteniendo contenedores..."
docker compose down

 echo "Eliminando imágenes antiguas..."
 docker compose rm -f

echo "Construyendo contenedores..."
docker compose build

echo "Iniciando contenedores..."
docker compose up -d

# echo "Reiniciando contenedores..."
# docker compose restart file_user_proxy file_generator file_reader file_assistant tool_file_reader tool_file_generator file_swarm