import re
import mysql.connector
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Connect to the database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="facial_recognization"
)
cursor = db.cursor()

# Load the image and perform OCR
img = Image.open('image.jpg')
ocr_text = pytesseract.image_to_string(img)

# Extract the data from the OCR output
pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', ocr_text)
pan = pan_match.group(0) if pan_match else None

name_match = re.search(r'Name\s+(.+)', ocr_text)
name = name_match.group(1) if name_match else None

father_match = re.search(r"Father's\s+name\s+(.+)", ocr_text)
father_name = father_match.group(1) if father_match else None

dob_match = re.search(r'Date of Birth\s+(\d{2}/\d{2}/\d{4})', ocr_text)
dob = dob_match.group(1) if dob_match else None

gender_match = re.search(r'Gender\s+(\w+)', ocr_text)
gender = gender_match.group(1) if gender_match else None

# Read the photograph as binary data
with open('photo.jpg', 'rb') as f:
    photo = f.read()

# Insert the extracted data into the table
sql = "INSERT INTO image_data (pan, name, father_name, dob, gender, photograph) VALUES (%s, %s, %s, %s, %s, %s)"
val = (pan, name, father_name, dob, gender, photo)
cursor.execute(sql, val)
db.commit()

# Close the database connection
db.close()

# Print the extracted fields
print(f'PAN: {pan}')
print(f'Name: {name}')
print(f"Father's Name: {father_name}")
print(f'DOB: {dob}')
print(f'Gender: {gender}')
print(f'Photo length: {len(photo)} bytes')