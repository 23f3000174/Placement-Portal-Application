from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, User, Company, PlacementDrive, Application, Student
from functools import wraps
from datetime import datetime

company_bp = Blueprint('company', __name__)


def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        user = User.query.get(user_id)
        if not user or user.role != 'company':
            flash('Access denied. Company only.', 'danger')
            return redirect(url_for('auth.login'))
        company = Company.query.filter_by(user_id=user.id).first()
        if not company or company.approval_status != 'approved':
            flash('Your company is not approved yet.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@company_bp.route('/dashboard')
@company_required
def dashboard():
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    drives = PlacementDrive.query.filter_by(company_id=company.id)\
        .order_by(PlacementDrive.created_at.desc()).all()

    upcoming_drives = [d for d in drives if d.status in ('approved', 'pending')]
    closed_drives = [d for d in drives if d.status == 'closed']
    rejected_drives = [d for d in drives if d.status == 'rejected']

    total_applications = sum(
        Application.query.filter_by(drive_id=d.id).count() for d in drives
    )

    return render_template('company/dashboard.html',
        company=company,
        upcoming_drives=upcoming_drives,
        closed_drives=closed_drives,
        rejected_drives=rejected_drives,
        total_applications=total_applications,
        all_drives=drives
    )


@company_bp.route('/create_drive', methods=['GET', 'POST'])
@company_required
def create_drive():
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        salary = request.form.get('salary', '').strip()
        location = request.form.get('location', '').strip()
        deadline_str = request.form.get('application_deadline', '').strip()

        if not job_title:
            flash('Job title is required.', 'danger')
            return redirect(url_for('company.create_drive'))

        application_deadline = None
        if deadline_str:
            try:
                application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('company.create_drive'))
            if application_deadline < datetime.now().date():
                flash('Deadline not valid.', 'danger')
                return redirect(url_for('company.create_drive'))

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            salary=salary,
            location=location,
            application_deadline=application_deadline,
            status='pending'
        )
        db.session.add(drive)
        db.session.commit()
        flash('Placement drive created! Waiting for admin approval.', 'info')
        return redirect(url_for('company.dashboard'))

    return render_template('company/create_drive.html', company=company)


@company_bp.route('/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
@company_required
def edit_drive(drive_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        drive.job_title = request.form.get('job_title', drive.job_title).strip()
        drive.job_description = request.form.get('job_description', drive.job_description or '').strip()
        drive.eligibility_criteria = request.form.get('eligibility_criteria', drive.eligibility_criteria or '').strip()
        drive.salary = request.form.get('salary', drive.salary or '').strip()
        drive.location = request.form.get('location', drive.location or '').strip()
        deadline_str = request.form.get('application_deadline', '').strip()

        if deadline_str:
            try:
                drive.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        db.session.commit()
        flash('Drive updated successfully.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/edit_drive.html', drive=drive, company=company)


@company_bp.route('/close_drive/<int:drive_id>')
@company_required
def close_drive(drive_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))
    drive.status = 'closed'
    db.session.commit()
    flash('Drive marked as closed.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/delete_drive/<int:drive_id>')
@company_required
def delete_drive(drive_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted successfully.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drive/<int:drive_id>/applications')
@company_required
def drive_applications(drive_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    applications = Application.query.filter_by(drive_id=drive.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('company/drive_applications.html',
        drive=drive, applications=applications, company=company)


@company_bp.route('/application/<int:app_id>/update', methods=['POST'])
@company_required
def update_application(app_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    application = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.get(application.drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    new_status = request.form.get('status', '')
    remarks = request.form.get('remarks', '').strip()
    interview_mode = request.form.get('interview_mode', '').strip()

    if new_status in ['applied', 'shortlisted', 'interview', 'selected', 'rejected']:
        application.status = new_status
        application.remarks = remarks
        application.interview_mode = interview_mode
        db.session.commit()
        flash(f'Application status updated to "{new_status}".', 'success')

    return redirect(url_for('company.drive_applications', drive_id=drive.id))


@company_bp.route('/application/<int:app_id>/view')
@company_required
def view_application(app_id):
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()
    application = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.get(application.drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    student = Student.query.get(application.student_id)
    return render_template('company/view_application.html',
        application=application, student=student, drive=drive, company=company)


@company_bp.route('/profile', methods=['GET', 'POST'])
@company_required
def profile():
    user_id = session.get('user_id')
    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        company.company_name = request.form.get('company_name', company.company_name).strip()
        company.industry = request.form.get('industry', company.industry or '').strip()
        company.website = request.form.get('website', company.website or '').strip()
        company.hr_name = request.form.get('hr_name', company.hr_name or '').strip()
        company.hr_email = request.form.get('hr_email', company.hr_email or '').strip()
        company.hr_phone = request.form.get('hr_phone', company.hr_phone or '').strip()
        company.description = request.form.get('description', company.description or '').strip()
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('company.profile'))

    return render_template('company/profile.html', company=company)
