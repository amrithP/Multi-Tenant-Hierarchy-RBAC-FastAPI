import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

VALID_CLIENT_ID = os.getenv("VALID_CLIENT_ID")
VALID_CLIENT_SECRET = os.getenv("VALID_CLIENT_SECRET")

# MYSQL_USER = os.getenv("MYSQL_USER","root") #take from docker-compose.yml  or take from the default value beside it 
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD","rootpassword")
# MYSQL_HOST = os.getenv("MYSQL_HOST","db")
# MYSQL_PORT = os.getenv("MYSQL_PORT","3306")
# MYSQL_DATABASE = os.getenv("MYSQL_DATABASE","hierarchy_db")
#postgres
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_Password")
DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_NAME=os.getenv("DB_NAME")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

#load everything from dot env


#login validation(locking and failed attempts)
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_MINUTES", "15"))


# reset password 
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "15"))




REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

FRONTEND_RESET_URL = os.getenv("FRONTEND_RESET_URL")

#resend mail provider service 
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")