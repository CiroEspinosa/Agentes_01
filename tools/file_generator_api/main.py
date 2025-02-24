import uvicorn
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
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
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Carpeta para almacenar documentos generados

FILES_FOLDER = Path("/app/shared_files/")

class FileContentResponse(BaseModel):
    """Response model for extracted file text."""
    filename: str
    file_content: str
    additional_text: Optional[str] = None

class DocumentRequest(BaseModel):
    filename: Optional[str] = None
    content: Union[List[Dict[str, str]], str]
    
class PDFEditRequest(BaseModel):
    filename: str  # El nombre del archivo es obligatorio
    data: Dict[str, str]  # Diccionario con los campos a modificar

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

    return {"download_url": f"http://localhost:7121//files/download/{file_path.name}"}



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




@app.get("/pdf/fields/{filename}", summary="Obtener los campos rellenables de un PDF")
async def get_pdf_fields(filename: str) -> Dict[str, str]:
    """
    Recibe el nombre de un PDF ya almacenado y devuelve los nombres de los campos de formulario que pueden ser editados.
    """
    file_path = FILES_FOLDER / filename

    # Verificar si el archivo existe
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        # Abrir el PDF con PyMuPDF (fitz)
        doc = fitz.open(str(file_path))
        fields = {}

        # Obtener los campos del formulario
        for page in doc:
            for widget in page.widgets():  # Extraer los elementos de formulario
                if widget.field_name:
                    fields[widget.field_name] = ""

        return JSONResponse(content={"fields": fields})

    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al procesar el PDF: {str(e)}")
    
@app.post(
    "/pdf/edit/",
    summary="Edit form fields in a PDF and save it",
    description="""
    This endpoint allows the user to edit the form fields of a specified PDF by providing the field names and their corresponding values.

    **Example Request:**
    ```json
    {
        "filename": "form.pdf",
        "data": {
            "name": "John Doe",
            "date": "2025-02-21",
            "signature": "Approved"
        }
    }
    ```
    """,
)
async def edit_pdf(request: PDFEditRequest):
    """
    Receives the name of a PDF and a dictionary with the values to modify in the form fields.
    Returns the edited PDF.
    """
    filename = request.filename
    data = request.data
    file_path = FILES_FOLDER / filename
    output_path = FILES_FOLDER / f"edited_{filename}"

    if not file_path.is_file():
        logging.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        doc = fitz.open(str(file_path))
        total_fields = 0
        updated_fields = 0

        for page in doc:
            widgets = page.widgets() or page.annots()  # Intentar con annots() si widgets() está vacío

            if not widgets:
                logging.warning(f"No form fields found on page {page.number}")

            for widget in widgets:
                total_fields += 1
                logging.debug(f"Found field: {widget.field_name}, value before: {widget.get_text}")

                if widget.field_name and widget.field_name in data:
                    widget.text = data[widget.field_name]  # Modificar el texto del campo
                    widget.update()  # Aplicar el cambio
                    updated_fields += 1
                    logging.info(f"Updated field: {widget.field_name}, new value: {widget.get_text}")

        if updated_fields == 0:
            logging.warning("No fields were updated. Check if the field names match.")

        doc.save(str(output_path), incremental=False)  # Guardar cambios
        doc.close()

        logging.info(f"PDF edited successfully: {output_path}")
        return {"message": "PDF edited and saved", "edited_filename": f"edited_{filename}"}

    except Exception as e:
        logging.error(f"Error modifying the PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error modifying the PDF: {str(e)}")

    


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7122)
