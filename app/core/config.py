from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_path: str = "kost.db"
    debug: bool = True
    
    # Tajný klíč pro šifrování tokenů (v produkci by měl být dlouhý a náhodný)
    SECRET_KEY: str = "super-tajny-klic-ktery-nikdo-neuhadne-123456"
    
    # Algoritmus pro podpis JWT
    ALGORITHM: str = "HS256"
    
    # Platnost tokenu v minutách
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()