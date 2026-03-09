from flask import Flask, redirect, url_for, session
from models.models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'security_key_full_safe'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.sqlite3'

db.init_app(app)


@app.context_processor
def inject_user():
    user = None
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
    return dict(user=user)

from controllers.auth import auth_bp
from controllers.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')


@app.route('/')
def index():
    return redirect(url_for('auth.login'))


def create_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active_user=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin created, username = admin, password = admin123')


with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)
