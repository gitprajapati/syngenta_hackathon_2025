#models/seed.py
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from models.base_models import Role, Department, Region



roles = [
    "System Admin", "Department Manager", "Operations Supervisor",
    "Financial Analyst", "Compliance Officer", "Auditor",
    "Supplier Representative", "Data Engineer", "Team Lead", "Worker"
]

departments = [
    "Financial", "Operational", "Strategic",
    "Compliance", "Human Resources", "Information Technology"
]

regions = [
    "Canada", "Caribbean", "Central Africa", "Central America", "Central Asia",
    "East Africa", "East of USA", "Eastern Asia", "Eastern Europe", "North Africa",
    "Northern Europe", "Oceania", "South America", "South Asia", "South of USA",
    "Southeast Asia", "Southern Africa", "Southern Europe", "US Center",
    "West Africa", "West Asia", "West of USA", "Western Europe"
]

def seed_data():
    db: Session = SessionLocal()

    try:
        # Seed Roles
        for role_name in roles:
            if not db.query(Role).filter_by(name=role_name).first():
                db.add(Role(name=role_name))

        # Seed Departments
        for dept_name in departments:
            if not db.query(Department).filter_by(name=dept_name).first():
                db.add(Department(name=dept_name))

        # Seed Regions
        for region_name in regions:
            if not db.query(Region).filter_by(name=region_name).first():
                db.add(Region(name=region_name))

        db.commit()
        print("Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
