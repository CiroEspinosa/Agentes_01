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
    summary="Generate a document (Excel or PDF)",
    description="""Creates a document (Excel or PDF) based on the provided data.

    ### Example Request Body (Excel)
    ```json
    {
        "type": "excel",
        "filename": "sales_report",
        "content": [
            {"Date": "2024-02-12", "Product": "Laptop", "Price": "1200", "Quantity": "2"},
            {"Date": "2024-02-13", "Product": "Mouse", "Price": "25", "Quantity": "5"}
        ]
    }
    ```
    - The `content` field must be a **list of dictionaries**, where each dictionary represents a row.
    - The dictionary **keys must be strings** (column names).
    - The values can be strings or numbers.

    ### Example Request Body (PDF - HTML Format)
    ```json
    {
        "type": "pdf",
        "filename": "invoice",
        "content": "<html><head><style>
        body { font-family: Arial, sans-serif; }
        h1 { color: navy; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid black; padding: 5px; text-align: left; }
        </style></head>
        <body>
        <h1>Invoice</h1>
        <p>Client: John Doe</p>
        <table>
            <tr><th>Item</th><th>Price</th></tr>
            <tr><td>Keyboard</td><td>$50</td></tr>
            <tr><td>Monitor</td><td>$200</td></tr>
        </table>
        </body></html>"
    }
    ```
    - The `content` must be **a valid HTML string**.
    - **Inline styles are recommended** to ensure proper rendering.
    - Tables should use **border-collapse: collapse** for better readability.

    ---
    - `type`: `"excel"` or `"pdf"` (required).
    - `filename`: Custom name for the file (optional, defaults to a generated name).
    - `content`: Data for the document (required).
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

@app.get(
    "/files/list",
    summary="List generated documents",
    description="Lists all the generated documents available for download."
)
async def list_generated_files():
    """Lista los archivos generados en la carpeta `OUTPUT_FOLDER`."""
    try:
        # Obtener la lista de archivos en el directorio
        files = os.listdir(OUTPUT_FOLDER)

        # Filtrar solo los archivos (ignorando directorios)
        files = [f for f in files if os.path.isfile(os.path.join(OUTPUT_FOLDER, f))]

        # Crear una lista con las URL de descarga
        files_info = [{"filename": f, "download_url": f"/files/download/{f}"} for f in files]

        return {"files": files_info}

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



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7122)
