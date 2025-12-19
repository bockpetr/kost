import random
import sys
import os

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.db import Users, Role, Rocnik, Vino, Hodnoceni, UserRole
from app.core.security import get_password_hash

ODRUDY_BILE = [
    "Veltlínské zelené", "Müller Thurgau", "Ryzlink vlašský", "Ryzlink rýnský",
    "Pálava", "Sauvignon", "Chardonnay", "Tramín červený", "Rulandské šedé",
    "Muškát moravský", "Hibernal", "Sylvánské zelené", "Neuburské"
]

ODRUDY_MODRE = [
    "Frankovka", "Svatovavřinecké", "Zweigeltrebe", "Modrý Portugal",
    "Rulandské modré", "Cabernet Sauvignon", "Merlot", "Cabernet Moravia",
    "André", "Dornfelder", "Neronet"
]

SLADKOST = ["Suché", "Polosuché", "Polosladké", "Sladké"]

PRIVLASTKY = [
    "Jakostní", "Kabinet", "Pozdní sběr", "Výběr z hroznů", 
    "Výběr z bobulí", "Ledové", "Slámové", "Zemské víno", "VOC"
]

POZNAMKY = [
    "Příjemná ovocná chuť.", "Vyšší kyselinka, svěží.", "Barva sytá, vůně lesního ovoce.", 
    "Vynikající vzorek, doporučuji.", "Plochá chuť, krátká dochuť.", "TOP víno ročníku.",
    "Harmonické víno s tóny medu.", "Trochu drsnější tříslovina, vhodné k archivaci.",
    "Lehké letní víno."
]

NAMES_VINARI = ["Jan Novák", "Petr Svoboda", "Pavel Dvořák", "Marek Černý", "Tomáš Procházka", "Lukáš Veselý"]
NAMES_HODNOTITELE = ["Jiří Kučera", "Michal Horák", "František Němec", "Martin Pokorný"]
NAMES_VINHOD = ["Karel Malý", "Josef Hrdý", "František Veselý"]

def log(msg):
    print(f"[INFO] {msg}")

def create_rocniky(db):
    log("Vytvářím ročníky...")
    rocniky_data = [(2023, False), (2024, False), (2025, True)]
    rocniky_map = {}

    for rok, active in rocniky_data:
        r = Rocnik(rok=rok, is_active=active)
        db.add(r)
        db.flush()
        rocniky_map[rok] = r                      
    return rocniky_map

def create_users(db):
    log("Vytvářím uživatele...")
    
    role_vinar = db.query(Role).filter_by(nazev="Vinař").first()
    role_hodnotitel = db.query(Role).filter_by(nazev="Hodnotitel").first()
    
    if not role_vinar or not role_hodnotitel:
        print("CHYBA: Role neexistují. Spusť nejprve create_tables.py!")
        return []

    created_users = []

    def process_users(jmena_list, role_objs):
        for jmeno in jmena_list:
            prijmeni = jmeno.split()[-1].lower().translate(str.maketrans("áéěíóúůýžščířďťň", "aeeiouuyzscirdtn"))
            login = prijmeni
            
            if any(u.login == login for u in created_users):
                login += "2"

            if db.query(Users).filter_by(login=login).first():
                existing = db.query(Users).filter_by(login=login).first()
                created_users.append(existing)
                continue

            new_user = Users(
                login=login,
                jmeno=jmeno,
                password_hash=get_password_hash("test"),
                email=f"{login}@kost.cz",
                is_active=True
            )
            
            for role in role_objs:
                new_user.role.append(role)
            
            db.add(new_user)
            db.flush()
            created_users.append(new_user)

    process_users(NAMES_VINARI, [role_vinar])
    process_users(NAMES_HODNOTITELE, [role_hodnotitel])
    process_users(NAMES_VINHOD, [role_vinar, role_hodnotitel])

    return created_users

def create_wines_and_ratings(db, rocniky_map, users):
    pool_vinari = [u for u in users if any(r.nazev == "Vinař" for r in u.role)]
    pool_hodnotitele = [u for u in users if any(r.nazev == "Hodnotitel" for r in u.role)]

    for rok, rocnik_obj in rocniky_map.items():
        log(f"--- Generuji data pro rok {rok} ---")
        
        current_vinari = random.sample(pool_vinari, k=min(len(pool_vinari), 4))
        
        for vinar in current_vinari:
            pocet_vin = random.randint(3, 5)
            for _ in range(pocet_vin):
                
                typ_vina = random.choice(["bile", "cervene", "ruzove"])
                
                if typ_vina == "bile":
                    odruda = random.choice(ODRUDY_BILE)
                    barva = "Bílé"
                    nazev_base = odruda
                elif typ_vina == "cervene":
                    odruda = random.choice(ODRUDY_MODRE)
                    barva = "Červené"
                    nazev_base = odruda
                else:
                    odruda = random.choice(ODRUDY_MODRE)
                    barva = "Růžové"
                    nazev_base = f"{odruda} Rosé"

                sladkost = random.choice(SLADKOST)
                privlastek = random.choice(PRIVLASTKY)
                full_nazev = f"{nazev_base} {privlastek}"

                nove_vino = Vino(
                    nazev=full_nazev,
                    rok_sklizne=rok - 1,
                    barva=barva,
                    privlastek=privlastek,
                    odruda=odruda,
                    sladkost=sladkost,
                    rocnik_id=rocnik_obj.id,
                    vinar_id=vinar.id 
                )
                db.add(nove_vino)
                db.flush()

                hodnotitele = random.sample(pool_hodnotitele, k=min(len(pool_hodnotitele), 3))
                for ev in hodnotitele:
                    if ev.id == vinar.id:
                        continue
                    
                    hodnoceni = Hodnoceni(
                        body=random.randint(70, 96),
                        poznamka=random.choice(POZNAMKY),
                        vino_id=nove_vino.id,
                        hodnotitel_id=ev.id
                    )
                    db.add(hodnoceni)

def main():
    print("=== Spouštím generátor testovacích dat (ORM verze) ===")
    db = SessionLocal()

    rocniky = create_rocniky(db)
    users = create_users(db)
    
    create_wines_and_ratings(db, rocniky, users)
        
    db.commit()
    log("=== HOTOVO: Data úspěšně uložena do DB ===")
    db.close()

if __name__ == "__main__":
    main()