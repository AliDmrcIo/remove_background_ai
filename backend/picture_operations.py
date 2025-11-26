# imports
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from db.database import SessionLocal
from db.tables import Pictures
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from backend.auth import get_current_user
import base64

router = APIRouter(
    prefix = "/picture",
    tags = ["Picture Operations"]
)

# class without id
class PictureRequest(BaseModel):
    original_image: str
    processed_image: str

# connect db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]             # to let all functions inherite from get_db
user_dependency = Annotated[Session, Depends(get_current_user)] # to let all functions inherite from get_current_user. bu resimleri kim kaydediyor ona bağla

@router.get("/get-all")
async def get_all(user:user_dependency, db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not Authorized!")
    else:
        all_entries = db.query(Pictures.id, Pictures.timestamp).filter(Pictures.user_id==user.id).order_by(Pictures.id.desc()).all()
    return [{"id":entry.id, "date":entry.timestamp} for entry in all_entries]

# show that original picture - bu sayfa history_detail_page'de gösterilecek
@router.get("/get-original-picture/{picture_id}")
async def get_original_picture(picture_id:int, db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not Authorized!")
    else:
        original_picture = db.query(Pictures.original_image).filter(Pictures.id == picture_id).filter(Pictures.user_id == user.id).first()
        if original_picture is not None:
            return {"original_image":original_picture[0]}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Picture not found")

# show that processed picture - bu sayfa history_detail_page'de gösterilecek
@router.get("/get-processed-picture/{picture_id}")
async def get_processed_picture(picture_id: int, db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not Authorized!")
    else:
        processed_image = db.query(Pictures.processed_image).filter(Pictures.id == picture_id).filter(Pictures.user_id == user.id).first()
        if processed_image is not None:
            return {"processed_image":processed_image[0]}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Picture not found")

# send original picture to db
@router.post("/post-original-picture")
async def post_original_picture(db: db_dependency, user: user_dependency, original_picture: UploadFile=File(...)):
    original_picture = await original_picture.read() # Dosyayı oku ve Base64'e çevir
    base64_string = base64.b64encode(original_picture).decode("utf-8") # convert binary data to base64

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not Authorized")
    else:
        picture = Pictures(user_id=user.id, original_image=base64_string, processed_image=None)
        db.add(picture)
        db.commit()
        db.refresh(picture)
    return {"id": picture.id, "status": "saved_original"}


# send processed image to db - ai'ın arkaplanı kaldırdığı fotoyu db'ye yollaması zaman alacağından update ile yolluyoruz fotoyu. önce direkt orjinal fotoyu kaydediyoruz, ai return verince ise o kayıda gidip tekrar açıp null olan processed kısmını gelen image ile düzeltiyoruz
@router.put("/post-processed-picture/{picture_id}")
async def post_processed_picture(picture_id:int, user: user_dependency, db:db_dependency, processed_picture:UploadFile=File(...)):
    
    processed_picture = await processed_picture.read() # AI'ın return ettiği processed picture'ı oku ve Base64'e çevir
    base64_string = base64.b64encode(processed_picture).decode("utf-8")
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not Authorized!")
    else:
        processed_picture = db.query(Pictures).filter(Pictures.id == picture_id).filter(Pictures.user_id == user.id).first() # update the none processed entry in the latest row of our db with the ai's return

        if processed_picture is None:
            raise HTTPException(status_code=404, detail="Picture not found or you are not the owner")

        processed_picture.processed_image = base64_string # fill the none with AI's return
        db.commit()

    return {"status": "success", "id": picture_id}

# delete manually and automatically(when all parts has been finished)
@router.delete("/delete/{picture_id}") # history_page.py sayfasında delete butonuna basılınca bura devreye girecek
async def delete_manually(picture_id:int, user:user_dependency, db:db_dependency):
    picture = db.query(Pictures).filter(Pictures.id==picture_id).filter(Pictures.user_id == user.id).first()
    if picture is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No entry such this!")
    else:
        db.delete(picture)
        db.commit()