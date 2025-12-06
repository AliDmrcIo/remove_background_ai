from db.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func # tarihi otomatik eklemek için

class Users(Base):
    __tablename__= "users"

    id = Column(Integer, primary_key=True, index=True)
    google_sub_id = Column(String, unique=True, index=True)
    email = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # tarihin otomatik girilmesi adına


class Pictures(Base):
    __tablename__ = "pictures"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"))
    original_image  = Column(Text)
    processed_image = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) # tarihin otomatik girilmesi adına