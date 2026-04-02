"""İlk admin kullanıcısını oluşturur. Kullanım: python seed.py"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    email = 'admin@tarihtenliderllik.com'
    if User.query.filter_by(email=email).first():
        print(f'Admin ({email}) zaten mevcut.')
    else:
        admin = User(
            email=email,
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
            name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f'Admin oluşturuldu: {email} / admin123')
