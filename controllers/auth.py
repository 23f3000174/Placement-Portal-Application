from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, User, Company, Student

auth_bp = Blueprint('auth', __name__)


def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    if user:
        return redirect_by_role(user)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active_user:
            flash('Your account has been deactivated. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role == 'company':
            company = Company.query.filter_by(user_id=user.id).first()
            if company:
                if company.approval_status == 'pending':
                    flash('Your company registration is pending admin approval.', 'warning')
                    return redirect(url_for('auth.login'))
                elif company.approval_status == 'rejected':
                    flash('Your company registration has been rejected.', 'danger')
                    return redirect(url_for('auth.login'))
                elif company.approval_status == 'blacklisted':
                    flash('Your company has been blacklisted. Contact admin.', 'danger')
                    return redirect(url_for('auth.login'))

        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student and student.is_blacklisted:
                flash('Your account has been blacklisted. Contact admin.', 'danger')
                return redirect(url_for('auth.login'))

        session['user_id'] = user.id
        flash('Logged in successfully!', 'success')
        return redirect_by_role(user)

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if user:
        return redirect_by_role(user)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')

        if role not in ['company', 'student']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()

        if role == 'company':
            company = Company(
                user_id=user.id,
                company_name=request.form.get('company_name', '').strip(),
                industry=request.form.get('industry', '').strip(),
                website=request.form.get('website', '').strip(),
                hr_name=request.form.get('hr_name', '').strip(),
                hr_email=request.form.get('hr_email', '').strip(),
                hr_phone=request.form.get('hr_phone', '').strip(),
                description=request.form.get('description', '').strip(),
                approval_status='pending'
            )
            db.session.add(company)
            db.session.commit()
            flash('Company registered successfully! Please wait for admin approval.', 'info')

        elif role == 'student':
            cgpa_val = request.form.get('cgpa', '')
            grad_year_val = request.form.get('graduation_year', '')

            student = Student(
                user_id=user.id,
                full_name=request.form.get('full_name', '').strip(),
                email=request.form.get('email', '').strip(),
                phone=request.form.get('phone', '').strip(),
                department=request.form.get('department', '').strip(),
                roll_number=request.form.get('roll_number', '').strip(),
                cgpa=float(cgpa_val) if cgpa_val else None,
                graduation_year=int(grad_year_val) if grad_year_val else None,
                skills=request.form.get('skills', '').strip(),
            )
            db.session.add(student)
            db.session.commit()
            flash('Student registered successfully! You can now login.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


def redirect_by_role(user):
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'company':
        return redirect(url_for('company.dashboard'))
    elif user.role == 'student':
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))
