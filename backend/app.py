from datetime import datetime, date
from flask import Flask, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import smtplib
import os

# Load environment variables from .env
load_dotenv()

# Constants
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///enrollments.db")
FRONTEND_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# App/DB setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path='')
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URL
db.init_app(app)

# Model Definitions
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_name = db.Column(db.String(100), nullable=False)
    child_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
with app.app_context():
    db.create_all()


# Routes
@app.route('/')
def root():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/api/enroll", methods=["POST"])
def enrollment():
    form = request.get_json()
    if not form:
        return {"message": "Invalid request."}, 400

    # Validate required fields
    required = ["parent_name", "child_name", "dob", "gender", "email", "phone_number"]
    for field in required:
        if not form.get(field, "").strip():
            return {"message": f"Missing required field: {field}"}, 400

    try:
        birth_date = datetime.strptime(form["dob"], '%Y-%m-%d').date()
    except ValueError:
        return {"message": "Invalid date format."}, 400

    today = date.today()
    calculated_age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    try:
        new_enrollment = Enrollment(
            parent_name = form["parent_name"].strip(),
            child_name = form["child_name"].strip(),
            dob = birth_date,
            age = calculated_age,
            gender = form["gender"].strip(),
            email = form["email"].strip(),
            phone_number = form["phone_number"].strip(),
            message = form.get("message", "").strip()
        )
        db.session.add(new_enrollment)
        db.session.commit()
        send_email(new_enrollment)
        db.session.close()

        message = "Enrollment submitted successfully!"
        status = 200
    except Exception as e:
        db.session.rollback()
        db.session.close()
        print(f"Error: {e}")
        message = "Enrollment failed. Please try again."
        status = 500
    finally:
        db.session.remove()

    return {"message": message}, status

# Helpers
def send_email(enrollment_data):
    # Configuration
    smtp_server = "smtp.gmail.com" # Or your provider
    smtp_port = 587
    sender_email = os.getenv("MAIL_USERNAME")
    receiver_email = os.getenv("MAIL_RECIPIENT") # The admin email
    password = os.getenv("MAIL_PASSWORD")

    # Create the email container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"New Enrollment: {enrollment_data.child_name}"

    # Format the body nicely (escape user input to prevent HTML injection)
    body = f"""
    <h2>New Enrollment Received</h2>
    <hr>
    <p><strong>Parent Name:</strong> {escape(enrollment_data.parent_name)}</p>
    <p><strong>Child Name:</strong> {escape(enrollment_data.child_name)}</p>
    <p><strong>DOB:</strong> {enrollment_data.dob}</p>
    <p><strong>Age:</strong> {enrollment_data.age}</p>
    <p><strong>Gender:</strong> {escape(enrollment_data.gender)}</p>
    <p><strong>Email:</strong> {escape(enrollment_data.email)}</p>
    <p><strong>Phone:</strong> {escape(enrollment_data.phone_number)}</p>
    <p><strong>Message:</strong><br>{escape(enrollment_data.message or '')}</p>
    <hr>
    <p>Sent at: {datetime.now()}</p>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Secure the connection
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {type(e).__name__}: {e}")
