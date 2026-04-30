from run import app
from app.extensions import db, bcrypt
from app.models.teacher import Teacher

with app.app_context():
    email = "demo@geoface.io"
    demo = Teacher.query.filter_by(email=email).first()
    if not demo:
        print(f"Registering demo teacher: {email}")
        password_hash = bcrypt.generate_password_hash("DemoPass@123").decode("utf-8")
        # Dummy encoding
        encoding = [0.0] * 512
        
        demo = Teacher(
            full_name="Demo Teacher",
            email=email,
            password_hash=password_hash,
            face_encoding=encoding,
            is_active=True
        )
        db.session.add(demo)
        db.session.commit()
        print("Demo teacher registered successfully.")
    else:
        print(f"Demo teacher already exists: {email}")
