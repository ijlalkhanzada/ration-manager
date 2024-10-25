# Ration Manager

## Overview

The Ration Manager is a Flask web application designed to manage recipient records for ration distribution. It allows users to add, update, delete, and view records, as well as upload data from Excel files and NIC images. This application is built using Flask, SQLAlchemy, and Tesseract OCR for image processing.

## Features

- User authentication with Flask-Login
- CRUD operations for recipient records
- Upload and process data from Excel files
- Upload NIC images and extract text using OCR
- Manual input of recipient data
- Activation and deactivation of members
- Filter records based on various criteria
- Delete duplicate records

## Requirements

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Pandas
- Pillow
- Pytesseract (Tesseract OCR)
- SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ijlalkhanzada/ration-manager.git
   ```

2. Navigate to the project directory:
   ```bash
   cd ration-manager
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Tesseract OCR:
   - Install Tesseract OCR on your system. [Installation guide](https://github.com/tesseract-ocr/tesseract).
   - Make sure to configure the Tesseract path in your code if necessary.

5. Create the database:
   - The application will automatically create the necessary database tables when it runs for the first time.

## Running the Application

1. Run the application:
   ```bash
   python app.py
   ```

2. Access the application in your web browser at `http://127.0.0.1:5000`.

## Usage

1. **Login**: Use the username and password to log in (default: admin/password).
2. **Display Records**: View all recipient records, filter them, or add new records.
3. **Upload Data**: Upload Excel files or NIC images to populate the database with recipient data.
4. **Manage Records**: Edit, activate, deactivate, or delete recipient records as needed.
5. **Duplicate Records**: Remove duplicate entries from the records.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to improve the application.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Micro web framework for Python.
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and Object-Relational Mapping (ORM) system for Python.
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open-source OCR engine.
