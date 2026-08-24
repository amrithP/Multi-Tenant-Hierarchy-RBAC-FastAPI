from app import models  
from app.db.database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)