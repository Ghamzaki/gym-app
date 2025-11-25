# app/models.py
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

## --- User Model ---

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String(50), default="member") # admin, trainer, member
    is_active = Column(Boolean, default=True)

    # Relationships
    # Classes taught by this user (if role is 'trainer')
    classes_taught = relationship("DBClass", back_populates="trainer")
    # Bookings made by this user (if role is 'member' or 'admin')
    bookings_made = relationship("DBBooking", back_populates="member")


## --- Class Model ---

class DBClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Foreign Key linking to the DBUser who is the trainer
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    max_capacity = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Relationships
    # Link back to the trainer user object
    trainer = relationship("DBUser", back_populates="classes_taught")
    # Link to all bookings for this class
    bookings = relationship("DBBooking", back_populates="class_data")


## --- Booking Model ---

class DBBooking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key linking to the class being booked
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    # Foreign Key linking to the user making the booking
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    # Link back to the class object
    class_data = relationship("DBClass", back_populates="bookings")
    # Link back to the user/member object
    member = relationship("DBUser", back_populates="bookings_made")