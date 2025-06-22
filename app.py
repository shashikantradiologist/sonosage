from flask import Flask, render_template, request, redirect, send_from_directory
import json
import os
from datetime import datetime
from xhtml2pdf import pisa


app = Flask(__name__)


# File paths
WORKLIST_FILE = 'worklist.json'
REPORT_FOLDER = 'reports'
os.makedirs(REPORT_FOLDER, exist_ok=True)

# Load and save worklist

def load_worklist():
    if os.path.exists(WORKLIST_FILE):
        with open(WORKLIST_FILE, 'r') as f:
            return json.load(f)
    return []

def save_worklist(worklist):
    with open(WORKLIST_FILE, 'w') as f:
        json.dump(worklist, f, indent=2)

worklist = load_worklist()

@app.route('/')
def home():
    return redirect('/reception')

@app.route('/reception', methods=['GET', 'POST'])
def reception():
    if request.method == 'POST':
        new_patient = {
            "name": request.form['name'],
            "age": request.form['age'],
            "sex": request.form['sex'],
            "ref_doc": request.form['ref_doc'],
            "study": request.form['study'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report": ""
        }
        worklist.append(new_patient)
        save_worklist(worklist)
    return render_template('reception.html', patients=worklist)

@app.route('/radiologist')
def radiologist():
    return render_template('radiologist.html', patients=worklist)

@app.route('/report/<int:index>', methods=['GET', 'POST'])
def report(index):
    if index >= len(worklist):
        return "Patient not found", 404

    patient = worklist[index]

    if request.method == 'POST':
        report_text = request.form['report_text']
        patient['report'] = report_text
        save_worklist(worklist)
        return redirect('/radiologist')

    return render_template('report.html', patient=patient, index=index)

from xhtml2pdf import pisa  # 🔁 New import

@app.route('/download/<int:index>')
def download_report(index):
    if index >= len(worklist):
        return "Invalid patient index", 404

    patient = worklist[index]

    # 🔹 Render the HTML report using Jinja2
    rendered = render_template('report_pdf.html', patient=patient)

    # 🔹 Define the PDF filename
    filename = f"{patient['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_output_path = os.path.join(REPORT_FOLDER, filename)

    # 🔹 Create a PDF using xhtml2pdf and save it to file
    with open(pdf_output_path, "wb") as result_file:
        pisa.CreatePDF(rendered, dest=result_file)

    # 🔹 Send the PDF back to the user
    return send_from_directory(REPORT_FOLDER, filename, as_attachment=True)


@app.route('/preview_pdf/<int:index>')
def preview_pdf(index):
    if index >= len(worklist):
        return "Patient not found", 404

    patient = worklist[index]
    filename_prefix = patient['name'].replace(' ', '_')
    reports = os.listdir(REPORT_FOLDER)
    matched_file = next((f for f in reports if f.startswith(filename_prefix)), None)

    print("DEBUG → Matched file:", matched_file)  # Debug log

    if not matched_file:
        return "PDF not found. Please generate it first."

    return render_template('preview_pdf.html', filename=matched_file)


@app.route('/static_pdf/<filename>')
def static_pdf(filename):
    return send_from_directory(REPORT_FOLDER, filename)

@app.template_filter('nl2br')
def nl2br(value):
    return value.replace('\n', '<br>')

if __name__ == '__main__':
    app.run(debug=True)
