import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
import uuid
from typing import List, Dict, Optional, Union
from xhtml2pdf import pisa
from io import BytesIO

app = FastAPI()

# Carpeta para almacenar documentos generados
OUTPUT_FOLDER = "generated_files"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

class DocumentRequest(BaseModel):
    type: str  # "excel" o "pdf"
    content: Union[List[Dict[str, str]], str]
    filename: Optional[str] = None

@app.post(
    "/files/generate/",
    summary="Generate a document",
    description="""Generates a document (Excel or PDF) based on the provided data.

    **Example Request Body (Excel):**
    ```json
    {
        "type": "excel",
        "filename": "my_report",
        "content": [
            {"col1": "Hello", "col2": "World"},
            {"col1": "Test", "col2": "excel"}
        ]
    }
    ```

    **Example Request Body (PDF - HTML Format):**
    ```json
    {
        "type": "pdf",
        "filename": "report",
        "content": "<html><body><h1>Report</h1><p>This is a test PDF</p></body></html>"
    }
    ```

    - The `type` field must be either "excel" or "pdf".
    - The `filename` field is optional. If provided, it will be used as the file name (without extension).
    - For **Excel**, `content` must be a list of dictionaries representing tabular data.
    - For **PDF**, `content` must be a valid **HTML string** with inline styles if needed.
    """
)
async def generate_document(data: DocumentRequest):
    """Genera un documento Excel o PDF con los datos proporcionados."""
    try:
        if not data.content:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos")

        # Si no se proporciona un nombre de archivo, generar uno único
        filename = data.filename if data.filename else f"document_{str(uuid.uuid4())[:8]}"
        file_path = os.path.join(OUTPUT_FOLDER, filename)

        # Crear el archivo en el formato deseado
        if data.type == "excel":
            if not isinstance(data.content, list):  # Validar que sea una lista
                raise HTTPException(status_code=400, detail="El contenido de Excel debe ser una lista de diccionarios.")
            file_path += ".xlsx"
            generate_excel(file_path, data.content)

        elif data.type == "pdf":
            if not isinstance(data.content, str):  # Validar que sea un string
                raise HTTPException(status_code=400, detail="El contenido de PDF debe ser un string HTML válido.")
            file_path += ".pdf"
            generate_pdf(file_path, data.content)

        else:
            raise HTTPException(status_code=400, detail="Formato no soportado")

        return {"download_url": f"/files/download/{os.path.basename(file_path)}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/files/download/{filename}",
    summary="Download a generated document",
    description="Allows downloading a previously generated document by specifying its filename."
)
async def download_file(filename: str):
    """Permite descargar un documento generado."""
    file_path = os.path.join(OUTPUT_FOLDER, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(file_path, filename=os.path.basename(filename), headers={"Content-Disposition": "attachment"})

def generate_excel(filename, content):
    """Genera un archivo Excel con los datos proporcionados."""
    df = pd.DataFrame(content)
    df.to_excel(filename, index=False, engine="openpyxl")

def generate_pdf(filename, content):
    """Genera un archivo PDF basado en contenido HTML proporcionado utilizando xhtml2pdf."""
    if not isinstance(content, str):
        raise ValueError("El contenido debe ser una cadena HTML válida.")
    
    # Convertir el HTML a PDF usando xhtml2pdf
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(content, dest=pdf_buffer)

    if pisa_status.err:
        raise ValueError("Hubo un error al generar el PDF con xhtml2pdf.")

    # Escribir el PDF generado en un archivo
    with open(filename, "wb") as pdf_file:
        pdf_file.write(pdf_buffer.getvalue())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7122)
