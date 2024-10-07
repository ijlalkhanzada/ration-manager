from flask import Flask, render_template, request
import pandas as pd
import pytesseract
from PIL import Image
import sqlite3

app = Flask(__name__)

# ہوم پیج
@app.route('/')
def index():
    return render_template('index.html')

# ایکسل فائل اپلوڈ کرنے کا فنکشن
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded!', 400
    file = request.files['file']
    df = pd.read_excel(file)
    # ڈیٹا پروسیس کریں اور ڈپلیکیٹ چیک کریں
    df.drop_duplicates(subset='Name', inplace=True)
    return render_template('display.html', data=df.to_dict(orient='records'))

# شناختی کارڈ کی تصویر سے ڈیٹا نکالیں
@app.route('/upload_cnic', methods=['POST'])
def upload_cnic():
    if 'file' not in request.files:
        return 'No file uploaded!', 400
    file = request.files['file']
    image = Image.open(file)
    text = pytesseract.image_to_string(image)
    # آپ یہاں سے CNIC کی تفصیلات نکال سکتے ہیں
    return f'Extracted text: {text}'

if __name__ == '__main__':
    app.run(debug=True)
