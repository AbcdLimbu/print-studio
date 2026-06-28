from app import create_app
from app.models import db, Admin
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    existing = Admin.query.filter_by(username='admin').first()
    if existing:
        print("Admin already exists!")
    else:
        admin = Admin(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created successfully!")
        print("Username: admin")
        print("Password: admin123")
