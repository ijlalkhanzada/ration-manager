# Ration Manager

## Description
Ration Manager is a Flask-based web application designed for managing ration distribution records. The application allows users to upload Excel files containing recipient data, upload NIC files for data extraction, manually input records, update existing records, and manage the active status of recipients. It also includes a user authentication system for secure access.

## Features
- User authentication with login/logout functionality.
- Upload Excel files to add recipient records.
- Upload NIC images and extract relevant data using OCR.
- Manually input recipient data.
- Update existing records.
- Activate or deactivate recipients.
- Delete duplicate records.
- Filter records based on names, addresses, or other criteria.
- User-friendly interface with Bootstrap for a responsive design.
- Support for uploading member images and NIC images for better record management.
- Comprehensive filtering system that allows searching by multiple criteria (name, city, house, contact number) using a single input.
- Enhanced error handling and user feedback mechanisms.
cl
## Technologies Used
- Flask: A micro web framework for Python.
- Pandas: For handling and manipulating Excel files.
- PIL and Pytesseract: For image processing and OCR functionality.
- Bootstrap: For creating responsive web pages.
- Flask-Login: For user authentication.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ijlalkhanzada/ration-manager.git
   cd ration-manager