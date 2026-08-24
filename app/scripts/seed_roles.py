from app.db.database import SessionLocal
from app.models import Role

ROLES = ["Owner", "Manager", "Employee"]

db = SessionLocal()
try:
    for name in ROLES:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name))
    db.commit()
    print("Roles seeded.")
finally:
    db.close()  #this file will be crucial in setting hierarchy 