import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import pandas as pd
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename

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
@app.route('/display', methods=['GET', 'POST'])
@login_required
def display_records():
    global all_records
    filter_value = request.args.get('filter', '').strip().lower()  # Use .args to get query params
    filtered_records = all_records

    if filter_value:
        filtered_records = [
            record for record in all_records if (
                filter_value in str(record.get('Name', '')).lower() or 
                filter_value in str(record.get('Father Name', '')).lower() or 
                filter_value in str(record.get('Address', '')).lower() or 
                filter_value in str(record.get('Contact Number', '')).lower()
            )
        ]

    return render_template('display_records.html', records=filtered_records)


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

        # Add is_active key to each record
        for record in records:
            record['is_active'] = True  # Set as active by default

        all_records.extend(records)

        return redirect(url_for('display_records'))

    return render_template('upload_excel.html')  # Render the upload form

def extract_field_from_nic(nic_data, field_name):
    # Simplified extraction logic (You need to define how your data is structured)
    for line in nic_data.split('\n'):
        if field_name.lower() in line.lower():
            return line.split(":")[-1].strip()  # Assuming the format is 'Name: value'
    return "Not Found"

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

        # Extract text from the NIC image using Tesseract
        nic_data = pytesseract.image_to_string(Image.open(nic_file_path))

        # Process NIC data and extract specific fields (Name, Father Name, etc.)
        name = extract_field_from_nic(nic_data, 'Name')
        father_name = extract_field_from_nic(nic_data, 'Father Name')
        address = extract_field_from_nic(nic_data, 'Address')
        contact_number = extract_field_from_nic(nic_data, 'Contact Number')

        # Create a record dynamically from extracted fields
        records = [{
            'Name': name,
            'Father Name': father_name,
            'Address': address,
            'Contact Number': contact_number,
            'is_active': True  # Set as active by default
        }]

        # Add to the global list of records
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

        # Create a folder for the member
        member_folder = os.path.join(UPLOAD_FOLDER, name.replace(" ", "_"))
        os.makedirs(member_folder, exist_ok=True)

        # Handle file uploads for NIC Front, NIC Back, and Member Image
        member_image = request.files.get('member_image')
        nic_front = request.files.get('nic_front')
        nic_back = request.files.get('nic_back')

        # Store manual input data
        record = {
            'Name': name,
            'Father Name': father_name,
            'Address': address,
            'Contact Number': contact_number,
            'is_active': True  # Set as active by default
        }
# Use os.path.join to ensure correct path formation
        member_folder = os.path.join(UPLOAD_FOLDER, name.replace(" ", "_"))
# Save the member image
        if member_image and allowed_file(member_image.filename):
            member_filename = secure_filename(member_image.filename)
            member_image.save(os.path.join(member_folder, member_filename))
            record['Member Image'] = os.path.join(name.replace(" ", "_"), member_filename).replace("\\", "/")  # Convert any backslashes to forward slashes

        if nic_front and allowed_file(nic_front.filename):
            front_filename = secure_filename(nic_front.filename)
            nic_front.save(os.path.join(member_folder, front_filename))
            record['NIC Front'] = os.path.join(name.replace(" ", "_"), front_filename)

        if nic_back and allowed_file(nic_back.filename):
            back_filename = secure_filename(nic_back.filename)
            nic_back.save(os.path.join(member_folder, back_filename))
            record['NIC Back'] = os.path.join(name.replace(" ", "_"), back_filename)

        all_records.append(record)

        return redirect(url_for('display_records'))

    return render_template('manual_input.html')  # Render the manual input form

# Allowed file formats
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Use forward slashes in URLs
    filename = filename.replace("\\", "/")
    return send_from_directory(UPLOAD_FOLDER, filename)


# Update route
# Update route
# Update route
@app.route('/update/<int:record_id>', methods=['GET', 'POST'])
@login_required
def update_record(record_id):
    global all_records

    # Ensure that the record_id is within the valid range
    if record_id >= len(all_records) or record_id < 0:
        flash('Record not found. Invalid record ID.')
        return redirect(url_for('display_records'))  # Redirect to display page if invalid ID
    
    if request.method == 'POST':
        # Update details
        all_records[record_id]['Name'] = request.form['name']
        all_records[record_id]['Father Name'] = request.form['father_name']
        all_records[record_id]['Address'] = request.form['address']
        all_records[record_id]['Contact Number'] = request.form['contact_number']
        
        # Member folder path
        member_folder = os.path.join(UPLOAD_FOLDER, all_records[record_id]['Name'].replace(" ", "_"))
        os.makedirs(member_folder, exist_ok=True)  # Ensure the folder exists

        # Handle file uploads if they exist
        member_image = request.files.get('member_image')
        nic_front = request.files.get('nic_front')
        nic_back = request.files.get('nic_back')

        if member_image and allowed_file(member_image.filename):
            member_filename = secure_filename(member_image.filename)
            member_image.save(os.path.join(member_folder, member_filename))
            all_records[record_id]['Member Image'] = os.path.join(all_records[record_id]['Name'].replace(" ", "_"), member_filename).replace("\\", "/")

        # Update routes mein NIC Front aur Back ka path forward slashes mein convert karen
        if nic_front and allowed_file(nic_front.filename):
         front_filename = secure_filename(nic_front.filename)
         nic_front.save(os.path.join(member_folder, front_filename))
         all_records[record_id]['NIC Front'] = os.path.join(all_records[record_id]['Name'].replace(" ", "_"), front_filename).replace("\\", "/")

        if nic_back and allowed_file(nic_back.filename):
            back_filename = secure_filename(nic_back.filename)
            nic_back.save(os.path.join(member_folder, back_filename))
            all_records[record_id]['NIC Back'] = os.path.join(all_records[record_id]['Name'].replace(" ", "_"), back_filename).replace("\\", "/")

        flash('Record updated successfully!')
        return redirect(url_for('display_records'))

    # If GET request, display the form with the current record details
    record = all_records[record_id]
    return render_template('update.html', record=record, record_id=record_id)


@app.route('/duplicates')
def show_duplicates():
    # یہاں آپ ڈپلیکیٹ ریکارڈز کی منطق لکھیں
    duplicates = get_duplicate_records()   # اپنی منطق کے مطابق اس فنکشن کو لکھیں
    return render_template('duplicates_display.html', duplicates=duplicates)

# Toggle active status route
@app.route('/toggle_status/<int:record_id>')
@login_required
def toggle_status(record_id):
    global all_records
    all_records[record_id]['is_active'] = not all_records[record_id]['is_active']  # Toggle the status
    return redirect(url_for('display_records'))

# Delete route
@app.route('/delete/<int:record_id>')
@login_required
def delete_record(record_id):
    global all_records
    del all_records[record_id]
    return redirect(url_for('display_records'))

# Delete duplicates route
@app.route('/delete_duplicates', methods=['GET', 'POST'])
@login_required
def delete_duplicates():
    global all_records
    seen = set()
    unique_records = []

    for record in all_records:
        # Use .get() method to avoid KeyError
        name = record.get('Name', '')
        father_name = record.get('Father Name', '')
        address = record.get('Address', '')
        contact_number = record.get('Contact Number', '')

        identifier = (name, father_name, address, contact_number)
        if identifier not in seen:
            seen.add(identifier)
            unique_records.append(record)

    all_records = unique_records
    flash('Duplicate records deleted successfully!')
    return redirect(url_for('display_records'))


if __name__ == '__main__':
    app.run(debug=True)