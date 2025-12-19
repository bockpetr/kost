from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from enum import Enum

class UserBase(BaseModel):
    """Společné atributy pro Uživatele."""
    login: str = Field(..., max_length=50, description="Unikátní přihlašovací jméno")
    jmeno: str = Field(..., max_length=100, description="Celé jméno uživatele")
    email: EmailStr = Field(..., max_length=100)
    adresa: Optional[str] = Field(None, max_length=200)
    telefon: Optional[str] = Field(None, max_length=20)
    is_active: bool = True

class UserCreate(UserBase):
    """Použije se při registraci. Obsahuje heslo v čistém textu."""
    password: str = Field(..., min_length=5, description="Heslo (nebude uloženo, jen hash)")

class UserRead(UserBase):
    """Použije se pro zobrazení uživatele. Neobsahuje heslo, ale má ID."""
    id: int
    model_config = ConfigDict(from_attributes=True) 

class BarvaVina(str, Enum):
    cervene = "Červené"
    bile = "Bílé"
    ruzove = "Růžové"

class SladkostVina(str, Enum):
    suche = "Suché"
    polosuche = "Polosuché"
    polosladke = "Polosladké"
    sladke = "Sladké"
    
class PrivlastekVina(str, Enum):
    jakostni = "Jakostní"
    kabinet = "Kabinet"
    pozdnisber = "Pozdní sběr"
    vyberzhroznu = "Výběr z hroznů" 
    vyberzbobuli = "Výběr z bobulí"
    ledove = "Ledové"
    slamove = "Slámové"
    zemskevino = "Zemské víno"
    voc = "VOC"

class VinoBase(BaseModel):
    """Společné atributy pro Víno."""
    nazev: str = Field(..., max_length=100)
    barva: Optional[BarvaVina] = None
    odruda: Optional[str] = Field(None, max_length=50)
    privlastek: Optional[PrivlastekVina] = None
    sladkost: Optional[SladkostVina] = None
    rok_sklizne: Optional[int] = Field(None, ge=1900, le=2100)

class VinoCreate(VinoBase):
    """Použije se při vkládání nového vína."""
    rocnik_id: int

class VinoRead(VinoBase):
    """Kompletní model vína vč. IDček, jak je v databázi."""
    id: int
    vinar_id: int
    rocnik_id: int

    model_config = ConfigDict(from_attributes=True)

class VinoDetail(VinoRead):
    vinar: Optional[UserRead] = None
    
class VinoWithStats(VinoDetail):
    """
    Model pro zobrazení vína v seznamu včetně vypočítaných statistik.
    Dědí z VinoDetail, takže obsahuje i vnořený objekt 'vinar'.
    """
    prumer_body: float = 0.0
    pocet_hodnoceni: int = 0