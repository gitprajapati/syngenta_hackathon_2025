#core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./test.db') 
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'a_very_secret_key')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    ROOT_USER_INITIAL_PWD : str = os.getenv("ROOT_USER_INITIAL_PWD", "rootpassword")
    SYN_MODEL_API_KEY : str = os.getenv('SYN_MODEL_API_KEY', 'your_SYN_MODEL_API_KEY')
    VECTOR_STORE_PATH : str = os.getenv('VECTOR_STORE_PATH', './vector_store/faiss_index')
    METADATA_PATH : str = os.getenv('METADATA_PATH', './vector_store/metadata.pkl')
    GROK_API_KEY: str = os.getenv('GROK_API_KEY')


    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()