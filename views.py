import pandas as pd
from flask import Blueprint, request, redirect, url_for, flash
from models import Recipient
from app import db

views = Blueprint('views', __name__)

@views.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    try:
        # Process the Excel file
        df = pd.read_excel(file)
        for index, row in df.iterrows():
            recipient = Recipient(
                name=row['Name'],
                address=row['Address'],
                contact_number=row['Contact'],
            )
            db.session.add(recipient)

        db.session.commit()
        flash('Records successfully added.')
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
    
    return redirect(url_for('views.dashboard'))
