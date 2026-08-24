import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

VALID_CLIENT_ID = os.getenv("VALID_CLIENT_ID")
VALID_CLIENT_SECRET = os.getenv("VALID_CLIENT_SECRET")

MYSQL_USER = os.getenv("MYSQL_USER","root") #take from docker-compose.yml  or take from the default value beside it 
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD","rootpassword")
MYSQL_HOST = os.getenv("MYSQL_HOST","db")
MYSQL_PORT = os.getenv("MYSQL_PORT","3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE","hierarchy_db")

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

#load everything from dot env
