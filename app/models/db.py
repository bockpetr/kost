from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Role(Base):
    __tablename__ = "ROLE"
    id = Column(Integer, primary_key=True, index=True)
    nazev = Column(String(50), nullable=False)

class Users(Base):
    __tablename__ = "USERS"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    jmeno = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    adresa = Column(String(200))
    telefon = Column(String(20))
    email = Column(String(100), nullable=False)
    
    role = relationship("Role", secondary="USERROLE", back_populates="users")
    vina = relationship("Vino", back_populates="vinar", cascade="all, delete-orphan")
    hodnoceni = relationship("Hodnoceni", back_populates="hodnotitel", cascade="all, delete-orphan")

class UserRole(Base):
    __tablename__ = "USERROLE"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("USERS.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("ROLE.id"), nullable=False)

class Rocnik(Base):
    __tablename__ = "ROCNIK"
    id = Column(Integer, primary_key=True, index=True)
    rok = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False)
    
    vina = relationship("Vino", back_populates="rocnik", cascade="all, delete-orphan")

class Vino(Base):
    __tablename__ = "VINO"
    id = Column(Integer, primary_key=True, index=True)
    nazev = Column(String(100), nullable=False)
    barva = Column(String(20))
    odruda = Column(String(50))
    privlastek = Column(String(50))
    sladkost = Column(String(20))
    rok_sklizne = Column(Integer)
    
    vinar_id = Column(Integer, ForeignKey("USERS.id"), nullable=False)
    rocnik_id = Column(Integer, ForeignKey("ROCNIK.id"), nullable=False)
    
    vinar = relationship("Users", back_populates="vina")
    rocnik = relationship("Rocnik", back_populates="vina")
    hodnoceni = relationship("Hodnoceni", back_populates="vino", cascade="all, delete-orphan")

class Hodnoceni(Base):
    __tablename__ = "HODNOCENI"
    id = Column(Integer, primary_key=True, index=True)
    body = Column(Integer)
    poznamka = Column(Text)
    
    vino_id = Column(Integer, ForeignKey("VINO.id"), nullable=False)
    hodnotitel_id = Column(Integer, ForeignKey("USERS.id"), nullable=False)
    
    vino = relationship("Vino", back_populates="hodnoceni")
    hodnotitel = relationship("Users", back_populates="hodnoceni")