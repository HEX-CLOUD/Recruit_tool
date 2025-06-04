import streamlit as st
import pytesseract
from PIL import Image
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cv2
import numpy as np

# --- CONFIGURATION ---

# Set path to Tesseract executable (update this path in your local environment)
TESSERACT_CMD_PATH = r"<PATH_TO_TESSERACT_EXECUTABLE>"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH

# Google Sheets API setup
# Place your Google service account credentials JSON file path here
GOOGLE_CREDS_JSON = "<PATH_TO_YOUR_CREDS_JSON_FILE>"

# Google Sheets document name
GOOGLE_SHEET_NAME = "<YOUR_GOOGLE_SHEET_NAME>"

# --- AUTHENTICATION ---

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, scope)
client = gspread.authorize(credentials)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1  # Adjust if using different sheet

# --- FUNCTIONS TO EXTRACT FIELDS ---

def extract_email(text):
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    return emails[0] if emails else ""

def extract_phone(text):
    phones = re.findall(r'\+?\d[\d\s\-\(\)]{7,}\d', text)
    return phones[0] if phones else ""

def extract_skills(text):
    skills_list = [
        'Python', 'Java', 'SQL', 'Excel', 'Machine Learning', 'Deep Learning', 'NLP',
        'Communication', 'Leadership', 'Teamwork', 'C++', 'JavaScript', 'Project Management',
        'Cloud', 'AWS', 'Azure', 'Docker', 'Kubernetes', 'React', 'Node.js'
    ]
    found = []
    for skill in skills_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found.append(skill)
    return ', '.join(found)

def extract_name(text):
    lines = text.split('\n')
    keywords = ['email', 'phone', 'contact', 'mobile', 'address', 'profile']
    for line in lines:
        if all(k not in line.lower() for k in keywords):
            words = line.strip().split()
            cap_words = [w for w in words if w and w[0].isupper()]
            if 1 < len(cap_words) <= 4:
                return line.strip()
    return ""

def extract_experience(text):
    exp = re.findall(r'(\d+)[+ ]*years?', text, re.IGNORECASE)
    return exp[0] if exp else ""

def extract_role(text):
    roles = ['Manager', 'Engineer', 'Developer', 'Analyst', 'Consultant', 'Director', 'Executive', 'Designer']
    for role in roles:
        match = re.search(role, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return ""

# --- STREAMLIT APP UI ---

st.title("RecruitOCR: Resume Information Extractor")

uploaded_file = st.file_uploader("Upload Resume Image (JPG, PNG, JPEG)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Resume Image", use_container_width=True)

    # Preprocess image for better OCR accuracy
    img_cv = np.array(image.convert('RGB'))
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    processed_image = Image.fromarray(thresh)

    # Extract text from image
    text = pytesseract.image_to_string(processed_image)
    st.subheader("Extracted Text")
    st.text_area("", text, height=200)

    # Parse key information from text
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    role = extract_role(text)
    experience = extract_experience(text)
    skills = extract_skills(text)

    parsed_data = {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Role": role,
        "Experience (Years)": experience,
        "Skills": skills
    }

    st.subheader("Parsed Resume Information")
    st.json(parsed_data)

    # Button to upload parsed data to Google Sheet
    if st.button("Upload to Google Sheet"):
        try:
            sheet.append_row([name, email, phone, role, experience, skills])
            st.success("Data successfully uploaded to Google Sheet!")
        except Exception as e:
            st.error(f"Failed to upload data: {e}")
