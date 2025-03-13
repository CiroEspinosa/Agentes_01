# Imagen base con Alpine Linux
FROM python:3.12.4-slim

# Definir el directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY tools/file_reader_api /app
COPY coreagents/factory/web_factory.py /app/factory/web_factory.py
COPY coreagents/utils/logging_config.py /app/utils/logging_config.py

# Setear el PYTHONPATH para asegurar que los módulos se encuentren
ENV PYTHONPATH=/app

# Exponer el puerto del servicio
EXPOSE 7121

# Iniciar la aplicación
ENTRYPOINT ["python3", "main.py"]
