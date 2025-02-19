import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
import uuid
from typing import List, Dict, Optional, Union
from xhtml2pdf import pisa
from io import BytesIO
from docx import Document
import requests
import logging
import traceback
from pdf2docx import Converter
import fitz
import pandas as pd
from openpyxl import load_workbook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Carpeta para almacenar documentos generados

FILES_FOLDER = Path("/storage/")
FILES_FOLDER.mkdir(parents=True, exist_ok=True) 

class FileContentResponse(BaseModel):
    """Response model for extracted file text."""
    filename: str
    file_content: str
    additional_text: Optional[str] = None

class DocumentRequest(BaseModel):
    content: Union[List[Dict[str, str]], str]
    filename: Optional[str] = None



def generate_unique_filename(base_name: Optional[str], extension: str) -> Path:
    """Genera un nombre de archivo único en la carpeta de destino."""
    filename = base_name if base_name else f"document_{uuid.uuid4().hex[:8]}"
    return FILES_FOLDER / f"{filename}{extension}"



def generate_excel(file_path: Path, content: list):
    """Genera un archivo Excel con los datos proporcionados."""
    df = pd.DataFrame(content)
    df.to_excel(file_path, index=False, engine="openpyxl")



@app.post(
    "/files/generate/txt/",
    summary="Generate a Text document",
    description="""Creates a Text document based on the provided text content.
    
    Example Request Body:
    ```json
    {
        "filename": "invoice",
        "content": "Invoice\nClient: John Doe\nItem: Keyboard\nPrice: $50"
    }
    ```
    """
)
async def generate_text_document(data: DocumentRequest):
    return await generate_document(data, ".txt", generate_txt)

def generate_txt(file_path: Path, text_content: str):
    """Generates a Text document from plain text content."""
    try:
        # Write the plain text content to a .txt file
        with open(file_path, 'w') as f:
            f.write(text_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Text document: {str(e)}")

@app.post(
    "/files/generate/pdf/",
    summary="Generate a PDF document",
    description="""Creates a PDF document based on the provided HTML content.
    Example Request Body (PDF - HTML Format)
    {
        "filename": "invoice",
        "content": "<html><head><style>
        body { font-family: Arial, sans-serif; }
        h1 { color: navy; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid black; padding: 5px; text-align: left; }
        </style></head><body>
        <h1>Invoice</h1>
        <p>Client: John Doe</p>
        <table>
            <tr><th>Item</th><th>Price</th></tr>
            <tr><td>Keyboard</td><td>$50</td></tr>
        </table>
        </body></html>"
    }
    """
)
async def generate_pdf_document(data: DocumentRequest):
    return await generate_document(data, ".pdf", generate_pdf)

def generate_pdf(file_path: Path, content: str):
    """Genera un archivo PDF basado en contenido HTML proporcionado utilizando xhtml2pdf."""
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(content, dest=pdf_buffer)
    if pisa_status.err:
        raise ValueError("Error al generar el PDF con xhtml2pdf.")
    file_path.write_bytes(pdf_buffer.getvalue())

@app.post(
    "/files/generate/excel/",
    summary="Generate an Excel document",
    description="""Creates an Excel document based on the provided data.
    Example Request Body (Excel)
    {
        "filename": "sales_report",
        "content": [
            {"Date": "2024-02-12", "Product": "Laptop", "Price": "1200", "Quantity": "2"},
            {"Date": ... }
        ]
    }
    """
)
async def generate_excel_document(data: DocumentRequest):
    return await generate_document(data, ".xlsx", generate_excel)




async def generate_document(data, file_extension: str, generator_function):
    """Genera un documento con el tipo y generador especificados."""
    if not data.content:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos")
    file_path = generate_unique_filename(data.filename, file_extension)
    generator_function(file_path, data.content)
    return {"download_url": f"/files/download/{file_path.name}"}

@app.post(
    "/files/generate/word/",
    summary="Generate a Word document",
    description="""Creates a Word document based on the provided HTML content.
    
    Example Request Body:
    ```json
    {
        "filename": "invoice",
        "content": "<html><head><style>
        body { font-family: Arial, sans-serif; }
        h1 { color: navy; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid black; padding: 5px; text-align: left; }
        </style></head><body>
        <h1>Invoice</h1>
        <p>Client: John Doe</p>
        <table>
            <tr><th>Item</th><th>Price</th></tr>
            <tr><td>Keyboard</td><td>$50</td></tr>
        </table>
        </body></html>"
    }
    ```
    """
)
async def generate_word_document(data: DocumentRequest):
    logger.info(f"📩 Recibida solicitud para generar DOCX: {data.filename}")
    return await generate_document(data, ".docx", generate_word)


async def generate_document(data, file_extension: str, generator_function):
    """Genera un documento con el tipo y generador especificados."""
    if not data.content:
        logger.error("❌ Error: No se proporcionaron datos en la solicitud.")
        raise HTTPException(status_code=400, detail="No se proporcionaron datos")

    file_path = generate_unique_filename(data.filename, file_extension)
    logger.info(f"📄 Nombre de archivo generado: {file_path}")

    try:
        generator_function(file_path, data.content)
        logger.info(f"✅ Documento generado con éxito: {file_path}")
    except Exception as e:
        logger.error(f"🔥 Error al generar el documento: {str(e)}")
        logger.error(traceback.format_exc())  # Capturar traceback completo
        raise HTTPException(status_code=500, detail=f"Error generating Word document: {str(e)}")

    return {"download_url": f"/files/download/{file_path.name}"}



def generate_word(file_path: Path, html_content: str):
    """Genera un DOCX desde HTML manteniendo estilos usando PDF como intermediario."""
    try:
        # Paso 1: Convertir HTML a PDF
        pdf_path = file_path.with_suffix(".pdf")
        with open(pdf_path, "wb") as pdf_file:
            pisa.CreatePDF(html_content, dest=pdf_file)

        # Paso 2: Convertir PDF a DOCX
        cv = Converter(str(pdf_path))
        cv.convert(str(file_path), start=0, end=None)
        cv.close()

        logger.info(f"📂 Archivo DOCX guardado en: {file_path}")

    except Exception as e:
        logger.error(f"🚨 Error en generate_word: {str(e)}")
        logger.error(traceback.format_exc())  # Capturar detalles del error
        raise HTTPException(status_code=500, detail=f"Error generating Word document: {str(e)}")

@app.get("/files/list",
    summary="List generated documents",
    description="Lists all the generated documents available for download.")
async def list_files():
    files = [
        {
            "filename": file.name,
            "download_url": f"/files/download/{file.name}"
        }
        for file in FILES_FOLDER.iterdir() if file.is_file()
    ]
    return {"files": files} if files else {"message": "No files stored.", "files": []}

@app.get("/files/text/{filename}", 
         response_model=FileContentResponse, 
         summary="Retrieve extracted file text", 
         description="Returns the plain text content of a previously uploaded file.")
async def get_file_content(filename: str):
    file_path = FILES_FOLDER / filename
    if file_path.exists() and file_path.is_file():
        try:
            return {"filename": filename, "file_content": file_path.read_text(encoding="utf-8")}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    raise HTTPException(status_code=404, detail="File not found.")

class FillRequest(BaseModel):
    data: Dict[str, str]

@app.post(
    "/files/fill/{filename}",
    summary="Fill placeholders in a document",
    description="""
    Fills placeholders in a document with the provided data and returns a download link.
    Supported formats: .docx, .xlsx, .pdf.
    
    Example Request Body:
    {
        "data": {"{{name}}": "John Doe", "{{date}}": "2025-02-14"}
    }
    """
)
async def fill_document(filename: str, request: FillRequest):
    """Rellena un documento con los datos proporcionados y devuelve un enlace de descarga."""

    file_path = FILES_FOLDER / filename
    filled_filename = f"filled_{uuid.uuid4().hex[:8]}_{filename}"
    filled_path = FILES_FOLDER / filled_filename

    # Intentar descargar el archivo desde múltiples servidores
    for server_port in [7121, 7122]:
        file_url = f"http://localhost:{server_port}/files/download/{filename}"
        try:
            response = requests.get(file_url, timeout=5)
            if response.status_code == 200:
                with open(file_path, "wb") as file:
                    file.write(response.content)
                break
        except requests.RequestException:
            continue
    else:
        raise HTTPException(status_code=404, detail="No se pudo obtener el archivo")

    # Determinar el tipo de archivo y aplicar el procesamiento adecuado
    extension = file_path.suffix.lower()
    try:
        if extension == ".docx":
            fill_word_document(file_path, filled_path, request.data)
        elif extension == ".xlsx":
            fill_excel_document(file_path, filled_path, request.data)
        elif extension == ".pdf":
            fill_pdf_document(file_path, filled_path, request.data)
        else:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

        return {"download_url": f"/files/download/{filled_filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

# --- Rellenar un documento Word ---
def fill_word_document(source: Path, destination: Path, data: dict):
    """Rellena los placeholders en un documento Word sin perder formato."""
    try:
        doc = Document(source)
        for para in doc.paragraphs:
            for run in para.runs:
                for key, value in data.items():
                    if key in run.text:
                        run.text = run.text.replace(key, value)
        doc.save(destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Word: {str(e)}")

# --- Rellenar un archivo Excel ---
def fill_excel_document(source: Path, destination: Path, data: dict):
    """Rellena los placeholders en un archivo Excel sin perder formato."""
    try:
        wb = load_workbook(source)
        ws = wb.active
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    for key, value in data.items():
                        cell.value = cell.value.replace(key, value)
        wb.save(destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Excel: {str(e)}")

# --- Rellenar un archivo PDF ---
def fill_pdf_document(source: Path, destination: Path, data: dict):
    """Rellena los placeholders en un archivo PDF."""
    try:
        pdf = fitz.open(source)
        for page in pdf:
            text = page.get_text("text")
            for key, value in data.items():
                text = text.replace(key, value)
            page.insert_text((50, 50), text, fontsize=12)

        pdf.save(destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en PDF: {str(e)}")

@app.get(
    "/files/download/{filename}",
    summary="Download a file",
    description="Allows downloading a document by specifying its filename."
)
async def download_file(filename: str):
    """Permite descargar un documento generado."""
    file_path = Path(FILES_FOLDER) / filename  
    if not file_path.is_file():  
        raise HTTPException(status_code=404, detail="Not Found")

    return FileResponse(file_path, filename=filename, headers={"Content-Disposition": "attachment"})



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7122)
