import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from pathlib import Path
from pydantic import BaseModel
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

app = FastAPI()

# Temporary storage for processed files
processed_files: Dict[str, str] = {}

# Pydantic Models
class FileContentResponse(BaseModel):
    filename: str
    file_content: str
    additional_text: Optional[str] = None

class FileProcessingResponse(BaseModel):
    message: str

# Helper functions

def read_pptx(file_path: Path) -> str:
    """Reads the content of a PPTX file."""
    presentation = Presentation(file_path)
    text = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)

def read_txt(file_path: Path) -> str:
    """Reads the content of a TXT file."""
    with file_path.open("r", encoding="utf-8") as f:
        return f.read()

def read_pdf(file_path: Path) -> str:
    """Reads the text of a PDF file."""
    pdf_text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        pdf_text += page.extract_text()
    return pdf_text

def read_docx(file_path: Path) -> str:
    """Reads the text of a DOCX file."""
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# Endpoints
@app.post(
    "/files/read/",
    response_model=FileContentResponse,
    summary="Read a file",
    description="Reads a file uploaded to the server and returns its content.",
)
async def read_file(file: UploadFile = File(...), additional_text: Optional[str] = Form(None)):
    """
    Endpoint to process a file uploaded to the server.
    """
    try:
        # Temporarily save the file
        temp_path = Path(f"/tmp/{file.filename}")
        with temp_path.open("wb") as f:
            f.write(await file.read())
        
        # Process the file based on its type
        file_extension = temp_path.suffix.lower()
        if file_extension == ".txt":
            file_content = read_txt(temp_path)
        elif file_extension == ".pdf":
            file_content = read_pdf(temp_path)
        elif file_extension == ".docx":
            file_content = read_docx(temp_path)
        elif file_extension == ".pptx":
            file_content = read_pptx(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
        
        # Store content in memory
        processed_files[file.filename] = file_content
        
        # Delete temporary file
        temp_path.unlink()

        return FileContentResponse(
            filename=file.filename,
            file_content=file_content,
            additional_text=additional_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the file: {str(e)}")

@app.get(
    "/files/content/{filename}",
    response_model=FileContentResponse,
    summary="Get file content",
    description="Returns the content of a previously processed file.",
)
async def get_file_content(filename: str):
    """
    Retrieves the content of a file that has already been processed.
    """
    if filename in processed_files:
        return FileContentResponse(
            filename=filename,
            file_content=processed_files[filename],
            additional_text=None,
        )
    else:
        raise HTTPException(status_code=404, detail="File not found.")

@app.get(
    "/files/list",
    summary="List processed files",
    description="Returns a list of the names of files that have been uploaded and processed.",
)
async def list_files():
    """
    Returns a list of processed files. If there are no files, a response with no files is provided.
    """
    if not processed_files:
        return {"message": "No files have been processed.", "files": []}
    return {"files": list(processed_files.keys())}

# Execution
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7121)
