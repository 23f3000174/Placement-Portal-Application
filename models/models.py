from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False) 
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        return self.is_active_user 

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String, nullable=False)
    industry = db.Column(db.String)
    website = db.Column(db.String)
    hr_name = db.Column(db.String)
    hr_email = db.Column(db.String)
    hr_phone = db.Column(db.String)
    description = db.Column(db.Text)
    approval_status = db.Column(db.String, default='pending') 

    user = db.relationship('User', backref=db.backref('company', uselist=False))
    drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade='all, delete-orphan')


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    department = db.Column(db.String)
    roll_number = db.Column(db.String)
    cgpa = db.Column(db.Float)
    graduation_year = db.Column(db.Integer)
    skills = db.Column(db.Text)
    resume_path = db.Column(db.String)
    is_blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('student', uselist=False))
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String, nullable=False)
    job_description = db.Column(db.Text)
    eligibility_criteria = db.Column(db.Text)
    salary = db.Column(db.String)
    location = db.Column(db.String)
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String, default='pending')  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, default='applied')  
    remarks = db.Column(db.Text)
    interview_mode = db.Column(db.String) 

    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),)
