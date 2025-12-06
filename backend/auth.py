"""burada authentication - login - signin işlemlerini yapacağız"""

import os
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from authlib.integrations.starlette_client import OAuth # Google bağlantısı için ana kütüphane
from dotenv import load_dotenv

# proje içindeki dosyalarım
from db.database import SessionLocal
from db.tables import Users

load_dotenv(override=True)

router = APIRouter(prefix = "/auth", tags=["Authentication"])

# .env dosyasından verileri çekiyoruz
SECRET_KEY = os.getenv("JWT_SECRET_KEY") # JWT; User'ın dijital kimlik kartıdır. içerisinde user id, user role, user expiration date gibi bilgiler bulunur. yani: websitemize girmeye çalışan bu kullanıcı bizim kullanıcımız mı kontrolü yapar
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL") # http://127.0.0.1:8501 (Streamlit adresi)

# 1. Google OAuth Ayarları
oauth = OAuth()
oauth.register(name="google", client_id=os.getenv("GOOGLE_CLIENT_ID"), client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
               server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration", 
               client_kwargs={"scope": "openid email profile"} # Google'dan hangi verileri istiyoruz?
               )

# 2. DB bağlantısı
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)] # database'e get, post, delete, update yapacak olan tüm fonksiyonların get_db, yani database'e bağlanma fonksiyonundan depend etmesini sağlayan satır

# 3. Token Oluşturma- Kullanıcı SignIn/Login olurken token oluşturma
def create_access_token(user_id:int, email:str, expires_delta: timedelta): # kullanıcıdan kayıt aşamasında aldığımız bilgileri koyuyoruz ve bu tokenin ne kadar süre aktif kalacağını da expires_delta ile belirtiyoruz
    payload = {"sub":email, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta # şu andan itibaren expires_delta süre boyunca geçerli olacak dedik
    payload.update({"exp": expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# 4. Token Doğrulama - Şu anki kullanıcıyı bulma
async def get_current_user(request: Request, db:Session = Depends(get_db)): # tokenin decoding(şifre çözme) kısmı. user'ın göndermiş olduğu token gerçekten var mı diye kontrol etme. Verify etme. Atılan isteklerin gerçekten bizim kullanıcılarımız tarafından gelip gelmediğini teyit edebilicez. Örneğin buradaki payload.get('id') sayesinde sadece o id'ye kayıtlı olan removedbackground fotolarını gösterebilcez
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail = "Please Login")
    
    # Token "Bearer " ile başlıyorsa temizle
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid User")
        user = db.query(Users).filter(Users.id == user_id).first() # Veritabanından kullanıcıyı teyit ediyoruz
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token not verified")
    
# 5. Google Endpoints

@router.get("/login") # Kullanıcı "Google ile Giriş Yap" butonuna bastığında buraya gelecek
async def login_via_google(request:Request):
    return await oauth.google.authorize_redirect(request, os.getenv("REDIRECT_URL")) # Kullanıcıyı Google'ın giriş sayfasına yönlendiriyoruz. İşlem bitince Google, kullanıcıyı REDIRECT_URL'e (bizim /auth callback'e) geri yollayacak.
    
@router.get("/callback") # Google işlem bitince buraya veri yollayacak (REDIRECT_URL burası)
async def auth_callback(request: Request, db:db_dependency):
    try:
        token = await oauth.google.authorize_access_token(request) # 1. Adım: Google'dan gelen kodu alıp Token'a çeviriyoruz (Access Token)
    except Exception as e:
        print(f"❌ Google Auth Error: {str(e)}")  # Debug log ekle
        raise HTTPException(status_code=400, detail=f"Google Auth Failed: {str(e)}")
    
    
    user_info = token.get("userinfo") # 2. Adım: Token içindeki kullanıcı bilgilerini alıyoruz (userinfo)

    if not user_info:
        user_info = await oauth.google.userinfo(token=token) # Bazen userinfo direkt token içinde gelmez, tekrar istek atmak gerekebilir (authlib genelde halleder)

    # google tokeninden gelen bilgileri al
    google_sub = user_info.get("sub") # Google'ın verdiği unique ID
    google_email = user_info.get("email")
    google_name = user_info.get("name")

    user = db.query(Users).filter(Users.google_sub_id == google_sub).first() # 3. Adım: Bu email veritabanımızda var mı?

    if not user: # KULLANICI BİZİM DB'DE YOKSA: Otomatik Kayıt Et (Sign Up mantığı)
        user = Users(
            google_sub_id=google_sub,
            email = google_email,
            full_name = google_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # DB'ye yeni kaydedilen kullanıcı verileriyle 60dklık bir token oluştur
    my_access_token = create_access_token(user_id=user.id, email = user.email, expires_delta=timedelta(minutes=60)) # Login SignIn esnasısnda burada token oluşturuluyor

    response = RedirectResponse(url=FRONTEND_URL) # google ile işimiz bittiğinde kullanıcıyı yönlendiriyoruz. Giriş işlemin bitti, hadi ana sayfaya
    response.set_cookie( # tokeni cookie'ye kaydediyoruz ki tokeni kullancıya verelim, o da girişte kullanabilsin tokenini, vermeseydik tokeni kullanamaz, dolaysıyla siteye giremezdi
        key="access_token",
        value=f"Bearer {my_access_token}",
        httponly=False,
        max_age=3600,  # 1800 -> 3600 yap
        samesite="lax",
        secure=False,
        domain=None  # Bu satırı ekle
    )
    print(f"✅ Login successful for: {google_email}")

    return response 
"""
Eğer Cookie'ye Kaydetmeseydim(response.set_cookie() yapmasaydım) Ne Olurdu?
Senaryoyu canlandıralım:
1. Kullanıcı Google ile giriş yaptı.
2. Senin backend'in my_access_token'ı üretti (Örn: "abc123xyz").
3. Ama set_cookie yapmadın. Sadece RedirectResponse döndün.

Sonuç: Kullanıcı Frontend sayfana (Streamlit) yönlenir. Kapıdaki görevli (senin get_current_user fonksiyonun) sorar:
"Hoşgeldin, giriş kartın (Token) nerede?"

Kullanıcı:
"Valla az önce arka tarafta üretildi ama bana kimse vermedi, elim boş geldim."

Dolayısıyla kullanıcının tekrar giriş yapması gerekir, yine aynı döngüye girer. asla siteye giremez
"""


@router.get("/logout")
async def logout():
    response = RedirectResponse(url = FRONTEND_URL)
    response.delete_cookie("access_token")
    return response


"""
Gerçek Hayat Senaryosunda Akış Nasıl Olacak?

1.  Kullanıcı Streamlit'te: Streamlit sayfanda "Google ile Giriş Yap" diye bir link veya buton olacak. Bu link `http://127.0.0.1:8000/auth/login` adresine gidecek.
2.  FastAPI (/auth/login): İstek geldiğinde, sunucu "Session" başlatır ve kullanıcıyı Google'ın güvenli giriş sayfasına (accounts.google.com...) fırlatır.
3.  Google Ekranı Kullanıcı Gmail hesabını seçer ve "İzin Ver" der.
4.  Dönüş (/auth/callback): Google, kullanıcıyı senin belirlediğin `http://127.0.0.1:8000/auth/callback` adresine geri gönderir. Yanında da özel bir "code" getirir.
5.  Takas ve Kayıt:
    *   Senin kodun bu "code"u Google'a geri verir, karşılığında kullanıcının `email` ve `name` bilgisini alır.
    *   Veritabanına bakar: "Bu mail bizde kayıtlı mı?".
    *   Yoksa: Kaydeder (Sign Up).
    *   Varsa: Bilgilerini çeker (Login).
6.  Final (Cookie & Redirect): Senin kodun bir JWT Token üretir, bunu bir hediye paketi (Cookie) içine koyar ve kullanıcıyı `FRONTEND_URL`'ye (Streamlit) geri postalar.
7.  Sonuç: Kullanıcı tekrar Streamlit sayfasını görür ama artık tarayıcısında senin verdiğin "access_token" çerezi vardır. 
           Streamlit üzerinden arka plana (FastAPI) bir istek attığında bu çerez otomatik gider ve `get_current_user` fonksiyonu "Evet, bu kullanıcı giriş yapmış" der.



Kısa özet:
1. Google ile Giriş Yap -> http://127.0.0.1:8000/auth/login
2. http://127.0.0.1:8000/auth/login -> Kullanıcı -> accounts.google.com
3. Gmail hesabını seç, ardından izin ver
4. Google -> email ve name ile birlikte http://127.0.0.1:8000/auth/callback adresine
5. Email ve name veritabanına kayıtlıysa Login, değilse SignIn
6. Token -> Cookie
"""