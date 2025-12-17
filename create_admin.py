import sys
import os

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.db import Users, Role
from app.core.security import get_password_hash

def create_admin():
    print("--- Vytváření Admina přes ORM ---")
    db = SessionLocal()
    
    print("Vytvářím uživatele 'admin'...")
    
    admin_role = db.query(Role).filter(Role.nazev == "Admin").first()
    password_hash = get_password_hash("admin")
        
    admin = Users(
        login="admin",
        password_hash=password_hash,
        jmeno="admin",
        email="admin@kost.cz",
        is_active=True
        )


    admin.role.append(admin_role)

    db.add(admin)
    db.commit()
    print(f"Uživatel 'admin' (heslo: admin) byl úspěšně vytvořen.")

    db.close()
    print("--- Hotovo ---")

if __name__ == "__main__":
    create_admin()