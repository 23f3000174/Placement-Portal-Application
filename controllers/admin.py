from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, User, Company, Student, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    pending_companies = Company.query.filter_by(approval_status='pending').count()
    pending_drives = PlacementDrive.query.filter_by(status='pending').count()
    approved_companies = Company.query.filter_by(approval_status='approved').count()
    approved_drives = PlacementDrive.query.filter_by(status='approved').count()
    placed_students = Application.query.filter_by(status='selected').count()

    recent_companies = Company.query.order_by(Company.id.desc()).limit(5).all()
    recent_students = Student.query.order_by(Student.id.desc()).limit(5).all()
    recent_applications = Application.query.order_by(Application.application_date.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        approved_companies=approved_companies,
        approved_drives=approved_drives,
        placed_students=placed_students,
        recent_companies=recent_companies,
        recent_students=recent_students,
        recent_applications=recent_applications
    )


@admin_bp.route('/companies')
@admin_required
def companies():
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        companies_list = Company.query.filter_by(approval_status=status_filter).all()
    else:
        companies_list = Company.query.all()
    return render_template('admin/companies.html', companies=companies_list, status_filter=status_filter)


@admin_bp.route('/company/<int:company_id>/approve')
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'approved'
    db.session.commit()
    flash(f'Company "{company.company_name}" has been approved.', 'success')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/reject')
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'rejected'
    db.session.commit()
    flash(f'Company "{company.company_name}" has been rejected.', 'warning')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/blacklist')
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'blacklisted'
    user = User.query.get(company.user_id)
    if user:
        user.is_active_user = False
    db.session.commit()
    flash(f'Company "{company.company_name}" has been blacklisted.', 'danger')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/activate')
@admin_required
def activate_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'approved'
    user = User.query.get(company.user_id)
    if user:
        user.is_active_user = True
    db.session.commit()
    flash(f'Company "{company.company_name}" has been re-activated.', 'success')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/delete')
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    db.session.delete(company)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Company deleted successfully.', 'info')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/students')
@admin_required
def students():
    students_list = Student.query.all()
    return render_template('admin/students.html', students=students_list)


@admin_bp.route('/student/<int:student_id>/blacklist')
@admin_required
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if student.is_blacklisted else 'activated'
    flash(f'Student "{student.full_name}" has been {status}.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/deactivate')
@admin_required
def deactivate_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    if user:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        status = 'deactivated' if not user.is_active_user else 'activated'
        flash(f'Student "{student.full_name}" account has been {status}.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/delete')
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Student deleted successfully.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/view')
@admin_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    applications = Application.query.filter_by(student_id=student.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('admin/view_student.html', student=student, applications=applications)


@admin_bp.route('/drives')
@admin_required
def drives():
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        drives_list = PlacementDrive.query.filter_by(status=status_filter).all()
    else:
        drives_list = PlacementDrive.query.all()
    return render_template('admin/drives.html', drives=drives_list, status_filter=status_filter)


@admin_bp.route('/drive/<int:drive_id>/approve')
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" has been approved.', 'success')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/reject')
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" has been rejected.', 'warning')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/close')
@admin_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'closed'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" has been closed.', 'info')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/view')
@admin_required
def view_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('admin/view_drive.html', drive=drive, applications=applications)


@admin_bp.route('/applications')
@admin_required
def applications():
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        apps = Application.query.filter_by(status=status_filter)\
            .order_by(Application.application_date.desc()).all()
    else:
        apps = Application.query.order_by(Application.application_date.desc()).all()
    return render_template('admin/applications.html', applications=apps, status_filter=status_filter)


@admin_bp.route('/search')
@admin_required
def search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')

    students_list = []
    companies_list = []

    if query:
        if search_type in ['all', 'students']:
            students_list = Student.query.filter(
                db.or_(
                    Student.full_name.ilike(f'%{query}%'),
                    Student.roll_number.ilike(f'%{query}%'),
                    Student.email.ilike(f'%{query}%'),
                    Student.phone.ilike(f'%{query}%'),
                    Student.department.ilike(f'%{query}%')
                )
            ).all()

        if search_type in ['all', 'companies']:
            companies_list = Company.query.filter(
                db.or_(
                    Company.company_name.ilike(f'%{query}%'),
                    Company.industry.ilike(f'%{query}%'),
                    Company.hr_name.ilike(f'%{query}%')
                )
            ).all()

    return render_template('admin/search_results.html',
        students=students_list, companies=companies_list,
        query=query, search_type=search_type)
