#services/root_user.py
from sqlalchemy.orm import Session
from models.base_models import User, Role
from core.config import settings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def create_root_user(db: Session):
    try:
        root_exists = db.query(
            db.query(User).filter(User.email == "root@syngenta.com").exists()
        ).scalar()

        if not root_exists:
            admin_role = db.query(Role).filter(Role.name == "System Admin").first()
            if not admin_role:
                admin_role = Role(name="System Admin")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)

            root_user = User(
                employee_id="SUPER-001",
                email="root@syngenta.com",
                role_id=admin_role.id,
                scope = "Global"
            )
            root_user.set_password(settings.ROOT_USER_INITIAL_PWD)

            db.add(root_user)
            db.commit()
            print("Root user created successfully")
        else:
            print("Root user already exists")

    except Exception as e:
        db.rollback()
        raise e
