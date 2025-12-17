from app.core.database import engine, Base, SessionLocal
from app.models.db import Role, Users

def init_db():

    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    roles = ["Admin", "Vinař", "Hodnotitel"]
    for role_name in roles:
        if not db.query(Role).filter_by(nazev=role_name).first():
            db.add(Role(nazev=role_name))
    db.commit()
    db.close()
    print("Databáze inicializována.")

if __name__ == "__main__":
    init_db()