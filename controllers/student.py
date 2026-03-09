from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, User, Student, PlacementDrive, Application, Company
from functools import wraps

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        user = User.query.get(user_id)
        if not user or user.role != 'student':
            flash('Access denied. Student only.', 'danger')
            return redirect(url_for('auth.login'))
        student = Student.query.filter_by(user_id=user.id).first()
        if student and student.is_blacklisted:
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@student_bp.route('/dashboard')
@student_required
def dashboard():
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()

    approved_drives = PlacementDrive.query.filter_by(status='approved')\
        .order_by(PlacementDrive.created_at.desc()).all()

    my_applications = Application.query.filter_by(student_id=student.id)\
        .order_by(Application.application_date.desc()).all()

    applied_drive_ids = [app.drive_id for app in my_applications]

    companies = Company.query.filter_by(approval_status='approved').all()

    return render_template('student/dashboard.html',
        student=student,
        approved_drives=approved_drives,
        my_applications=my_applications,
        applied_drive_ids=applied_drive_ids,
        companies=companies
    )


@student_bp.route('/drive/<int:drive_id>')
@student_required
def drive_detail(drive_id):
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)
    company = Company.query.get(drive.company_id)

    existing_application = Application.query.filter_by(
        student_id=student.id, drive_id=drive.id
    ).first()

    return render_template('student/drive_detail.html',
        drive=drive, company=company, student=student,
        existing_application=existing_application)


@student_bp.route('/company/<int:company_id>')
@student_required
def company_detail(company_id):
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    company = Company.query.get_or_404(company_id)
    drives = PlacementDrive.query.filter_by(company_id=company.id, status='approved').all()
    applied_drive_ids = [a.drive_id for a in Application.query.filter_by(student_id=student.id).all()]
    return render_template('student/company_detail.html',
        company=company, drives=drives, student=student,
        applied_drive_ids=applied_drive_ids)


@student_bp.route('/apply/<int:drive_id>', methods=['POST'])
@student_required
def apply_drive(drive_id):
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != 'approved':
        flash('This drive is not currently accepting applications.', 'warning')
        return redirect(url_for('student.dashboard'))

    existing = Application.query.filter_by(
        student_id=student.id, drive_id=drive.id
    ).first()
    if existing:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student.dashboard'))

    application = Application(
        student_id=student.id,
        drive_id=drive.id,
        status='applied'
    )
    db.session.add(application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student.applications'))


@student_bp.route('/applications')
@student_required
def applications():
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    my_apps = Application.query.filter_by(student_id=student.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('student/applications.html',
        student=student, applications=my_apps)


@student_bp.route('/history')
@student_required
def history():
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    all_apps = Application.query.filter_by(student_id=student.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('student/history.html',
        student=student, applications=all_apps)


@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        student.full_name = request.form.get('full_name', student.full_name).strip()
        student.email = request.form.get('email', student.email or '').strip()
        student.phone = request.form.get('phone', student.phone or '').strip()
        student.department = request.form.get('department', student.department or '').strip()
        student.roll_number = request.form.get('roll_number', student.roll_number or '').strip()
        cgpa = request.form.get('cgpa', '')
        student.cgpa = float(cgpa) if cgpa else student.cgpa
        grad_year = request.form.get('graduation_year', '')
        student.graduation_year = int(grad_year) if grad_year else student.graduation_year
        student.skills = request.form.get('skills', student.skills or '').strip()

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student)
