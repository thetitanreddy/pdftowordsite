import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pdf2docx import Converter

app = FastAPI()

# Mount the static folder to serve the HTML file
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

# --- PDF TO WORD ---
@app.post("/convert/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    filename = file.filename
    input_path = f"uploads/{filename}"
    output_filename = f"{filename.split('.')[0]}.docx"
    output_path = f"uploads/{output_filename}"

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convert
    try:
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        # Clean up the original PDF to save space
        os.remove(input_path)
    except Exception as e:
        return {"error": str(e)}

    return FileResponse(output_path, filename=output_filename, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
