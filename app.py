import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import pandas as pd
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename
import sqlite3
import pandas as pd
from models import Record  # Importing the Record model



def create_table():
    try:
        conn = sqlite3.connect('I:\\ration-manager\\ration_manager.db')
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                father_name TEXT NOT NULL,
                address TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                is_active BOOLEAN NOT NULL
            )
        ''')
        
        conn.commit()  # Changes ko save karein
        print("Table created successfully.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        conn.close()   # Connection band karein

def save_to_database(records):
    conn = sqlite3.connect('I:\\ration-manager\\ration_manager.db')
    cursor = conn.cursor()

    for record in records:
        print("Saving record:", record)  # Debugging line
        try:
            cursor.execute(''' 
                INSERT INTO recipient (name, father_name, address, contact_number, is_active) 
                VALUES (?, ?, ?, ?, ?) 
            ''', (
                record.get('Name').strip(),
                record.get('Father Name', "Not Found").strip(),
                record.get('Address', "Not Found").strip(),
                record.get('Contact Number', "Not Found"),
                record.get('is_active', True)
            ))
            print("Successfully inserted record:", record)  # Confirmation message
        except sqlite3.Error as e:
            print(f"Error inserting record {record}: {e}")

    conn.commit()
    conn.close()


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

@app.route('/replace_member')
def replace_member():
    member_id = request.args.get('member_id')  # Get the member ID from the query parameter
    old_member = Recipient.query.filter_by(id=member_id).first()  # Fetch the old member data

    if old_member:
        return render_template('replace_member.html', old_member=old_member)  # Pass the old member data to the template
    else:
        return "Member not found", 404  # Handle the case where the member does not exist

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
    # Fetch records from the database
    conn = sqlite3.connect('I:\\ration-manager\\ration_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipient")
    all_records = cursor.fetchall()  # Get all records from the database
    conn.close()

    # Apply filtering if a filter value is provided
    filter_value = request.args.get('filter', '').strip().lower()
    filtered_records = all_records

    if filter_value:
        filtered_records = [
            record for record in all_records if (
                filter_value in str(record[1]).lower() or  # Name
                filter_value in str(record[2]).lower() or  # Father Name
                filter_value in str(record[3]).lower() or  # Address
                filter_value in str(record[4]).lower()      # Contact Number
            )
        ]

    # Debugging: print the filtered records
    print("Filtered Records:", filtered_records)

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
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Save the uploaded Excel file
        file_path = os.path.join('uploads', secure_filename(file.filename))
        file.save(file_path)

        # Read the Excel file
        df = pd.read_excel(file_path)

        # Print column names for debugging
        print("Columns in the uploaded Excel file:", df.columns)

        records = df.to_dict(orient='records')

        # Add is_active key to each record
        for record in records:
            record['is_active'] = True  # Set as active by default

        # Save to database
        save_to_database(records)

        return redirect(url_for('display_records'))

    return render_template('upload_excel.html')  # Render the upload form



# Function to extract fields from NIC data using regex
def extract_field_from_nic(nic_data, field_name):
    field_pattern = rf'{field_name}[:\s]+([A-Za-z\s]+)'
    match = re.search(field_pattern, nic_data, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Not Found"

@app.route('/upload_nic', methods=['GET', 'POST'])
def upload_nic():
    global all_records
    if request.method == 'POST':
        if 'nic_file' not in request.files or request.files['nic_file'].filename == '':
            flash('No file selected.')
            return redirect(request.url)

        nic_file = request.files['nic_file']
        nic_file_path = os.path.join(UPLOAD_FOLDER, secure_filename(nic_file.filename))
        nic_file.save(nic_file_path)

        # Extract text from the NIC image using Tesseract
        nic_data = pytesseract.image_to_string(Image.open(nic_file_path))

        # Try extracting specific fields (Name, Father Name, etc.)
        name = extract_field_from_nic(nic_data, 'Name')
        
        # Handle KeyError for 'Father Name' gracefully
        try:
            father_name = extract_field_from_nic(nic_data, 'Father Name')
        except KeyError:
            father_name = "Not Found"

        address = extract_field_from_nic(nic_data, 'Address')
        contact_number = extract_field_from_nic(nic_data, 'Contact Number')

        records = [{
            'Name': name,
            'Father Name': father_name,
            'Address': address,
            'Contact Number': contact_number,
            'is_active': True
        }]

        all_records.extend(records)

        return redirect(url_for('display_records'))

    return render_template('upload_nic.html')


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
    record = Record.query.get(record_id)  # Fetching the record from the database
    if record:
        record.is_active = not record.is_active
        db.session.commit()  # Committing changes to the database
    return redirect(url_for('display_records'))  # Redirecting to the records display page


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


if __name__ == "__main__":
    create_table()  # Ensure this function is called before running the app
    app.run(debug=True)


