from datetime import datetime, date
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase

# Application/DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///enrollments.db"

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URL
CORS(app)
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
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/api/enroll", methods=["POST"])
def enrollment():
    form = request.get_json()

    birth_date = datetime.strptime(form["dob"], '%Y-%m-%d').date()
    today = date.today()
    calculated_age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    try:
        new_enrollment = Enrollment(
            parent_name = form["parent_name"],
            child_name = form["child_name"],
            dob = birth_date,
            age = calculated_age,
            gender = form["gender"],
            email = form["email"],
            phone_number = form["phone_number"],
            message = form["message"]
        )
        db.session.add(new_enrollment)
        db.session.commit()
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
