import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from typing import Optional, Dict
from pathlib import Path
from pydantic import BaseModel
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from odf.opendocument import load
from ebooklib import epub
from bs4 import BeautifulSoup
import pandas as pd
import pdfplumber
from pathlib import Path


app = FastAPI()

processed_files: Dict[str, str] = {}
structured_files: Dict[str, str] = {}

class FileContentResponse(BaseModel):
    """Response model for extracted file text."""
    filename: str
    file_content: str
    additional_text: Optional[str] = None

def read_file_content(file_path: Path) -> str:
    """Extracts the plain text content from a file."""
    file_extension = file_path.suffix.lower()
    try:
        if file_extension == ".txt":
            return file_path.read_text(encoding="utf-8")
        elif file_extension == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        elif file_extension == ".docx":
            return "\n".join(p.text for p in Document(file_path).paragraphs)
        elif file_extension == ".pptx":
            return "\n".join(shape.text for slide in Presentation(file_path).slides for shape in slide.shapes if hasattr(shape, "text"))
        elif file_extension == ".html":
            with open(file_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "html.parser").get_text()
        elif file_extension in [".xls", ".xlsx"]:
            excel_data = pd.read_excel(file_path, sheet_name=None)
            return "\n\n".join(f"Sheet: {sheet_name}\n{df.to_string(index=False)}" for sheet_name, df in excel_data.items())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    raise HTTPException(status_code=400, detail="Unsupported file format.")

@app.post("/files/upload/", 
          response_model=FileContentResponse, 
          summary="Upload and extract file text", 
          description="Uploads a file and extracts its plain text content.")
async def upload_file(file: UploadFile = File(...), additional_text: Optional[str] = Form(None)):
    temp_path = Path(f"/tmp/{file.filename}")
    try:
        temp_path.write_bytes(await file.read())
        file_content = read_file_content(temp_path)
        processed_files[file.filename] = file_content
        return FileContentResponse(filename=file.filename, file_content=file_content, additional_text=additional_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the file: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.get("/files/text/{filename}", 
         response_model=FileContentResponse, 
         summary="Retrieve extracted file text", 
         description="Returns the plain text content of a previously uploaded file.")
async def get_file_content(filename: str):
    if filename in processed_files:
        return FileContentResponse(filename=filename, file_content=processed_files[filename])
    raise HTTPException(status_code=404, detail="File not found.")

@app.get("/files/list", 
         summary="List uploaded files", 
         description="Returns the names of files that have been uploaded and processed.")
async def list_files():
    return {"files": list(processed_files.keys())} if processed_files else {"message": "No files have been processed.", "files": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7121)
