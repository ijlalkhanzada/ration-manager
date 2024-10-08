import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

import pandas as pd
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if not authenticated

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Sample users (replace with DB logic)
users = {'admin': 'password'}  # Example user: admin

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('display_records'))  # Redirect to display page after login
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Display page
@app.route('/display')
@login_required
def display_records():
    global all_records
    return render_template('display_records.html', records=all_records)

# Folder to save uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# List to store all records
all_records = []

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Excel upload route
@app.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    global all_records
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        # Save the uploaded Excel file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Read the Excel file
        df = pd.read_excel(file_path)
        records = df.to_dict(orient='records')
        all_records.extend(records)

        return redirect(url_for('display_records'))

    return render_template('upload_excel.html')  # Render the upload form

# NIC upload route
@app.route('/upload_nic', methods=['GET', 'POST'])
def upload_nic():
    global all_records
    if request.method == 'POST':
        if 'nic_file' not in request.files:
            return redirect(request.url)

        nic_file = request.files['nic_file']
        if nic_file.filename == '':
            return redirect(request.url)

        # Save and process the NIC image
        nic_file_path = os.path.join(UPLOAD_FOLDER, nic_file.filename)
        nic_file.save(nic_file_path)
        nic_data = pytesseract.image_to_string(Image.open(nic_file_path))

        # Process NIC data (simplified for example)
        records = [{'Name': 'Extracted Name', 'Father Name': 'Extracted Father Name', 'Address': 'Extracted Address', 'Contact Number': 'Extracted Contact Number'}]
        all_records.extend(records)

        return redirect(url_for('display_records'))

    return render_template('upload_nic.html')  # Render the upload form

# Manual input route
@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    global all_records
    if request.method == 'POST':
        name = request.form['name']
        father_name = request.form['father_name']
        address = request.form['address']
        contact_number = request.form['contact_number']

        # Store manual input data
        records = [{'Name': name, 'Father Name': father_name, 'Address': address, 'Contact Number': contact_number}]
        all_records.extend(records)

        return redirect(url_for('display_records'))

    return render_template('manual_input.html')  # Render the manual input form

# Update route
@app.route('/update/<int:record_id>', methods=['GET', 'POST'])
@login_required
def update_record(record_id):
    global all_records
    if request.method == 'POST':
        all_records[record_id]['Name'] = request.form['name']
        all_records[record_id]['Father Name'] = request.form['father_name']
        all_records[record_id]['Address'] = request.form['address']
        all_records[record_id]['Contact Number'] = request.form['contact_number']
        return redirect(url_for('display_records'))

    record = all_records[record_id]
    return render_template('update.html', record=record, record_id=record_id)

# Delete route
@app.route('/delete/<int:record_id>')
@login_required
def delete_record(record_id):
    global all_records
    del all_records[record_id]
    return redirect(url_for('display_records'))

# Delete duplicates route
@app.route('/delete_duplicates')
@login_required
def delete_duplicates():
    global all_records
    seen = set()
    unique_records = []
    for record in all_records:
        identifier = (record['Name'], record['Father Name'], record['Address'], record['Contact Number'])
        if identifier not in seen:
            seen.add(identifier)
            unique_records.append(record)
    all_records = unique_records
    flash('Duplicate records deleted successfully!')
    return redirect(url_for('display_records'))

if __name__ == '__main__':
    app.run(debug=True)
