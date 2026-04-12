import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_dev_key')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')
    DB_NAME = os.environ.get('DB_NAME', 'food_ordering_db')
    NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '')
