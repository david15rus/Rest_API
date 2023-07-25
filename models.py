import uuid

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Menu(Base):
    __tablename__ = "menus"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, index=True, unique=True)
    description = Column(String)

    submenus = relationship('SubMenu', back_populates='menu', cascade="all, delete-orphan")

class SubMenu(Base):
    __tablename__ = "submenus"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, index=True, unique=True)
    description = Column(String)
    menu_id = Column(UUID, ForeignKey("menus.id"))

    menu = relationship('Menu', back_populates='submenus')
    dishes = relationship('Dish', back_populates='submenu', cascade="all, delete-orphan")

class Dish(Base):
    __tablename__ = "dishes"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, index=True, unique=True)
    description = Column(String)
    price = Column(Float, index=True)
    submenu_id = Column(UUID, ForeignKey('submenus.id'))

    submenu = relationship('SubMenu', back_populates='dishes')
