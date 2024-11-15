import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, login_required, logout_user
import pandas as pd
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename
import sqlite3
import pandas as pd
from models import Record  # Importing the Record model
from models import Recipient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
import time
import secrets
from sqlalchemy.exc import OperationalError
from helpers import parse_excel
from uuid import uuid4  # Generate a unique link for sharing
from flask_migrate import Migrate

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
                True  # Set as active by default
            ))
            print("Successfully inserted record:", record)  # Confirmation message
        except sqlite3.Error as e:
            print(f"Error inserting record {record}: {e}")

    conn.commit()
    conn.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///I:/ration-manager/ration_manager.db'  # Database URI specified

db = SQLAlchemy(app)  # Initialize SQLAlchemy with Flask app
migrate = Migrate(app, db)  # مائیگریٹ انسٹینس


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    member_image = db.Column(db.String, nullable=True)  # نیا کالم برائے ممبر کی تصویر
    reference = db.Column(db.String(100), nullable=True)  # نیا کالم برائے ریفرنس
    is_active = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()
    
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id


# Sample users (replace with DB logic)
users = {'admin': 'admin'}  # Example user: admin

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
    
    # Fetch all recipients from the database
    recipients = Recipient.query.order_by(Recipient.id.desc()).all()

    # Apply filtering if a filter value is provided
    filter_value = request.args.get('filter', '').strip().lower()
    
    # Filter the records based on the filter value
    filtered_records = recipients  # Start with all records

    if filter_value:
        filtered_records = [
            record for record in recipients if (
                filter_value in record.name.lower() or  # Name
                filter_value in record.father_name.lower() or  # Father Name
                filter_value in record.address.lower() or  # Address
                filter_value in record.contact_number.lower()      # Contact Number
            )
        ]

    total_recipients = len(filtered_records)  # Total filtered records count

    return render_template('display_records.html', records=filtered_records, total_recipients=total_recipients)
# Folder to save uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# List to store all records
all_records = []
# Home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_excel', methods=['POST', 'GET'])
def upload_excel():
    if request.method == 'POST':
        file = request.files['excel_file']  # Excel file ko retrieve karna
        
        if file:
            # Excel file ko DataFrame mein read karna
            data = pd.read_excel(file)
            print(data.columns)  # Check the columns
            
            # Required columns ki check
            required_columns = ['S/ No', 'Name', 'Father Name', 'Contact Number', 'Address']
            missing_columns = [col for col in required_columns if col not in data.columns]

            if missing_columns:
                 missing_columns_list = ', '.join(missing_columns)
                 flash(f"Excel file mein ye columns nahi hain: {missing_columns_list}. Meharbani Farma kar unhein theek karain aur dobara upload karain.")
                 return redirect(url_for('upload_excel'))

            for col in required_columns:
                if col not in data.columns:
                    flash(f"Excel file mein '{col}' column nahi hai.")
                    return redirect(url_for('upload_excel'))

            # Har row mein member data check karna
            for index, row in data.iterrows():
                # NaN values ko handle karna
                if pd.isna(row['Name']) or pd.isna(row['Father Name']) or pd.isna(row['Address']):
                    flash(f"Row {index + 1}: Name, Father Name, aur Address fields zaroori hain.")
                    continue  # Skip this row if required fields are NaN

                contact_number = row['Contact Number'] if pd.notna(row['Contact Number']) else 'N/A'
                
                # Check karen ki member ID database mein already hai ya nahi
                existing_member = Recipient.query.filter_by(id=row['S/ No']).first()
                
                # Agar member already database mein hai
                if existing_member:
                    # Update existing member ka data agar koi changes hain
                    existing_member.name = row['Name']
                    existing_member.father_name = row['Father Name']
                    existing_member.address = row['Address']
                    existing_member.contact_number = contact_number
                    
                    # Agar member inactive hai to use active karen
                    if not existing_member.is_active:
                        existing_member.is_active = True
                else:
                    # Agar member already database mein nahi hai to naye member ko add karen
                    new_member = Recipient(
                        id=row['S/ No'],  # Using 'S/ No' for id
                        name=row['Name'],  # Using 'Name'
                        father_name=row['Father Name'],  # Using 'Father Name'
                        address=row['Address'],  # Using 'Address'
                        contact_number=contact_number,  # Using 'Contact Number'
                        is_active=True  # Naye member ko active status dena
                    )
                    db.session.add(new_member)
            
            # Database changes ko commit karna
            db.session.commit()
            flash("Naye members ya updated members add kar diye gaye hain!")
            
            return redirect(url_for('display_records'))

    return render_template('upload_excel.html')  # Render the upload form

all_records = []

# Generate link function
@app.route('/generate_link')
@login_required
def generate_link():
    # Generate token (random token ya hashed unique value bana sakte hain)
    token = secrets.token_urlsafe(16)
    
    # Store the token in session ya temporary storage mein
    session['shareable_token'] = token

    # Generated URL create karein
    shareable_url = url_for('manual_input', token=token, _external=True)

    # Manual input page par redirect aur generated link ke saath display karain
    return render_template('manual_input.html', shareable_url=shareable_url, show_generate_link=True)# Manual Input function
@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    # Agar POST request hai to form data handle karein
    if request.method == 'POST':
        name = request.form.get('name')
        father_name = request.form.get('father_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        reference = request.form.get('reference')

        # Image کو اپ لوڈ کریں
        member_image = request.files['member_image']
        member_image_filename = secure_filename(member_image.filename)
        member_image_path = os.path.join('static/images', member_image_filename)
        member_image.save(member_image_path)

        # Member ki ID ko check karne ke liye
        existing_member = Recipient.query.filter_by(name=name, father_name=father_name, contact_number=contact_number, reference=reference).first()

        if existing_member:
            flash("Yeh member pehle se database mein maujood hai.")
            return redirect(url_for('manual_input'))  # Wapas manual input form par redirect karein
        else:
            # Naye recipient ka record create karain
            new_recipient = Recipient(
                name=name, 
                father_name=father_name, 
                address=address, 
                contact_number=contact_number, 
                reference=reference,  # Reference ko add karein
                member_image=member_image_filename  # Member image ka naam save karein
            )

            # Database mein add aur commit karain
            db.session.add(new_recipient)
            db.session.commit()

            # Add karne ke baad confirmation page par redirect karein
            return render_template('confirmation.html', member=new_recipient, member_image_url=url_for('static', filename='images/' + new_recipient.member_image), reference=new_recipient.reference)

    # Agar GET request hai, tab ye check karein
    show_generate_link = current_user.is_authenticated  # Agar user login hai to link button dikhaye

    return render_template('manual_input.html', show_generate_link=show_generate_link)


# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    filename = filename.replace("\\", "/")
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/update/<int:record_id>', methods=['GET', 'POST'])
@login_required
def update_record(record_id):
    record = Recipient.query.get(record_id)
    print(f"Record found: {record}")  # Debugging line to check if the record is found

    if not record:
        flash("Record not found.")
        return redirect(url_for('display_records'))

    if request.method == 'POST':
        # Update the record fields with data from the form
        record.name = request.form['name']
        record.father_name = request.form['father_name']
        record.address = request.form['address']
        record.contact_number = request.form['contact_number']
        
        # Check if the activation checkbox is checked
        record.is_active = 'is_active' in request.form
        
        # Commit changes to the database
        db.session.commit()
        flash("Record updated successfully.")
        return redirect(url_for('display_records'))

    # Render the form with existing record details for GET requests
    return render_template('update.html', record=record)

@app.route('/activate_member/<int:record_id>')
@login_required
def activate_member(record_id):
    member = Recipient.query.get(record_id)
    if member:
        member.is_active = True  # Set member as active
        db.session.commit()  # Save changes
        flash("Member activated successfully")
    else:
        flash("Member not found")
    return redirect(url_for('display_records'))

@app.route('/deactivate_member/<int:record_id>')
@login_required
def deactivate_member(record_id):
    member = Recipient.query.get(record_id)
    if member:
        member.is_active = False  # Set member as inactive
        db.session.commit()  # Save changes
        flash("Member deactivated successfully")
    else:
        flash("Member not found")
    return redirect(url_for('display_records'))

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
@app.route('/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    record = Recipient.query.get(record_id)
    if record:
        db.session.delete(record)
        db.session.commit()
        flash("Record deleted successfully")
    else:
        flash("Record not found")
    return redirect(url_for('display_records'))

import os

if __name__ == "__main__":
    # Create the database table before running the server
    create_table()

    # Use the provided PORT environment variable or fallback to 5000
    port = int(os.environ.get("PORT", 5000))

    # Start the Flask application
    app.run(host="0.0.0.0", port=port, debug=True)



