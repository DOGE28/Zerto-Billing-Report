from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sgu_prod_url: str
    sgu_prod_secret: str
    boi_prod_url: str
    boi_prod_secret: str
    fb_prod_url: str
    fb_prod_secret: str

    class Config:
        env_file = '.env'
settings = Settings()

