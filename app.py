from flask import Flask
from models.models import db, User
from werkzeug.security import generate_password_hash

app=Flask(__name__)
app.config['SECRET_KEY'] = 'Full_security'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqllite:///mad1.db'
db.init_app(app)

@app.route('/')
def index():
    return "Welcome to mad1 project"

def create_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin=User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin created, username = admin, password = admin123')

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == "__main__":
    app.run(debug=True)
