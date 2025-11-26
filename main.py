"""burada fastapi routerlarını toplayacağız bir de diğer main işlemleri"""
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from db.database import engine, Base
from backend.auth import router as auth_router, get_current_user
from backend.picture_operations import router as picture_router
from db.tables import Users
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.include_router(auth_router)
app.include_router(picture_router)

@app.get("/test-user")
def read_current_user(user: Users = Depends(get_current_user)):
    return {
        "status": "Başarılı!",
        "mesaj": f"Merhaba {user.full_name}, seni tanıdım!",
        "email": user.email,
        "google_id": user.google_sub_id
    }

# --- TABLOLARI OLUŞTURMA KODU ---
# Bu komut çalıştığında Users ve Pictures, veritabanında tabloya dönüştürür.
Base.metadata.create_all(bind=engine)