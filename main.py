from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from starlette.responses import JSONResponse

from config import DATABASE_URL
from models import Base, Menu, SubMenu, Dish
from schemas.menu import MenuSchema, MenuSchemaAdd, MenuSchemaUpdate
from schemas.submenu import SubMenuSchema, SubMenuSchemaAdd, SubMenuSchemaUpdate
from schemas.dish import DishSchema, DishSchemaAdd, DishSchemaUpdate

app = FastAPI()

# Создаем соединение с базой данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы в базе данных
db = Base.metadata.create_all(bind=engine)


# Реализация операции Create для сущности Menu
@app.post("/api/v1/menus/", response_model=MenuSchema)
def create_menu(menu_data: MenuSchemaAdd):
    db = SessionLocal()
    new_menu = Menu(title=menu_data.title, description=menu_data.description)
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    return JSONResponse(
        content=
        {
            "id": str(new_menu.id),
            "title": new_menu.title,
            "description": new_menu.description
        },
        status_code=201)


# Реализация операции Read для всех сущностей Menu
@app.get("/api/v1/menus/", response_model=MenuSchema)
def read_menus(skip: int = 0, limit: int = 10):
    db = SessionLocal()
    menus = db.query(Menu).offset(skip).limit(limit).all()
    response_data = []
    for menu in menus:
        submenus_count = db.query(func.count(SubMenu.id)).filter(
            SubMenu.menu_id == menu.id).scalar()

        dishes_count = db.query(func.count(Dish.id)).join(SubMenu).filter(
            SubMenu.menu_id == menu.id).scalar()

        response_data.append(
            {
                "id": str(menu.id),
                "title": menu.title,
                "description": menu.description,
                "submenus_count": int(submenus_count),
                "dishes_count": int(dishes_count),
            }
        )
    return JSONResponse(content=response_data, status_code=200)


# Реализация операции Read для одной сущности Menu
@app.get("/api/v1/menus/{menu_id}", response_model=MenuSchema)
def read_one_menu(menu_id: str):
    db = SessionLocal()
    menu = db.query(Menu).filter(Menu.id == menu_id).first()

    # Обрабатываем случай, в котором меню еще не создано
    if not menu:
        raise HTTPException(status_code=404, detail="menu not found")

    # Определяем количество подменю в меню
    submenus_count = db.query(func.count(SubMenu.id)).filter(
        SubMenu.menu_id == menu_id).scalar()

    # Определяем количество блюд в меню
    subquery = db.query(func.count(Dish.id)).join(SubMenu).filter(
        SubMenu.menu_id == menu_id).subquery()
    dishes_count = db.query(func.sum(subquery)).scalar()

    return JSONResponse(
        content=
        {
            "id": str(menu.id),
            "title": menu.title,
            "description": menu.description,
            "submenus_count": int(submenus_count),
            "dishes_count": int(dishes_count),
        },
        status_code=200)


# Реализация операции Update для сущности Menu
@app.patch("/api/v1/menus/{menu_id}", response_model=MenuSchema)
def update_menu(menu_id: str, menu_data: MenuSchemaUpdate):
    db = SessionLocal()
    updated_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if updated_menu:
        updated_menu.title = menu_data.title
        updated_menu.description = menu_data.description
        db.commit()
        db.refresh(updated_menu)
        return JSONResponse(
        content=
        {
            "id": str(updated_menu.id),
            "title": updated_menu.title,
            "description": updated_menu.description,
        },
        status_code=200)


# Реализация операции Delete для сущности Menu
@app.delete("/api/v1/menus/{menu_id}", response_model=MenuSchema)
def delete_menu(menu_id: str):
    db = SessionLocal()

    removed_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if removed_menu:
        db.delete(removed_menu)
        db.commit()

        return JSONResponse(content={}, status_code=200)


# Реализация операции Create для сущности Submenu
@app.post("/api/v1/menus/{menu_id}/submenus", response_model=SubMenuSchema)
def create_submenu_for_menu(menu_id: str, submenu_data: SubMenuSchemaAdd):
    db = SessionLocal()

    # Проверка наличия меню в которое добавляется подменю
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="menu not found")

    # Проверка по критерию
    # невозможности нахождения подменю в разных меню одновременно
    existing_submenu = db.query(SubMenu).filter(SubMenu.menu_id != menu_id, SubMenu.title == submenu_data.title).first()
    if existing_submenu:
        raise HTTPException(status_code=400, detail="Submenu already belongs to ather menu")

    # При прохождении всех проверок
    # создается новый объект и добавляется в таблицу
    new_submenu = SubMenu(menu_id=menu_id,
                          title=submenu_data.title,
                          description=submenu_data.description)

    db.add(new_submenu)
    db.commit()
    db.refresh(new_submenu)
    return JSONResponse(
        content=
        {
            "id": str(new_submenu.id),
            "title": new_submenu.title,
            "description": new_submenu.description
        },
        status_code=201)


# Реализация операции Read для всех сущности Submenu
@app.get("/api/v1/menus/{menu_id}/submenus", response_model=SubMenuSchema)
def read_submenus_for_menu(menu_id: str, skip: int = 0, limit: int = 10):
    db = SessionLocal()
    submenus = db.query(SubMenu).filter(SubMenu.menu_id == menu_id).offset(skip).limit(limit).all()

    response_data = []
    for submenu in submenus:
        dishes_count = db.query(func.count(Dish.id)).filter(
            Dish.submenu_id == submenu.id).scalar()

        response_data.append(
            {
                "id": str(submenu.id),
                "title": submenu.title,
                "description": submenu.description,
                "dishes_count": int(dishes_count),
            }
        )
    return JSONResponse(content=response_data, status_code=200)


# Реализация операции Read для одной сущности Submenu
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}", response_model=SubMenuSchema)
def read_one_submenu_for_menu(menu_id: str, submenu_id: str):
    db = SessionLocal()
    submenu = db.query(SubMenu).filter(
        SubMenu.menu_id == menu_id, SubMenu.id == submenu_id).first()

    if not submenu:
        raise HTTPException(status_code=404, detail="submenu not found")

    dishes_count = db.query(func.count(Dish.id)).filter(
        Dish.submenu_id == submenu_id).scalar()

    return JSONResponse(
        content=
        {
            "id": str(submenu.id),
            "title": submenu.title,
            "description": submenu.description,
            "dishes_count": int(dishes_count),
        },
        status_code=200)


# Реализация операции Update для сущности Submenu
@app.patch("/api/v1/menus/{menu_id}/submenus/{submenu_id}", response_model=SubMenuSchema)
def update_submenu(menu_id: str, submenu_id: str, submenu_data: SubMenuSchemaUpdate):
    db = SessionLocal()
    updated_submenu = db.query(SubMenu).filter(SubMenu.menu_id == menu_id, SubMenu.id == submenu_id).first()
    if updated_submenu:
        updated_submenu.title = submenu_data.title
        updated_submenu.description = submenu_data.description
        db.commit()
        db.refresh(updated_submenu)
        return JSONResponse(
            content=
            {
                "id": str(updated_submenu.id),
                "title": updated_submenu.title,
                "description": updated_submenu.description,
            },
            status_code=200)


# Реализация операции Delete для сущности Submenu
@app.delete("/api/v1/menus/{menu_id}/submenus/{submenu_id}", response_model=SubMenuSchema)
def delete_submenu(menu_id: str, submenu_id: str):
    db = SessionLocal()
    removed_submenu = db.query(SubMenu).filter(SubMenu.menu_id == menu_id,
                                               SubMenu.id == submenu_id).first()
    if removed_submenu:
        db.delete(removed_submenu)
        db.commit()

        return JSONResponse(
        content={ },
        status_code=200)


# Реализация операции Create для сущности Dish
@app.post("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes", response_model=DishSchema)
def create_dish_for_submenu(menu_id: str, submenu_id: str, dish_data: DishSchemaAdd):
    db = SessionLocal()

    # Проверка наличия подменю в которое добавляется блюдо
    submenu = db.query(SubMenu).filter(SubMenu.menu_id == menu_id,
                                       SubMenu.id == submenu_id).first()
    if not submenu:
        raise HTTPException(status_code=404, detail="Submenu not found")

    # Проверка по критерию
    # невозможности нахождения блюда в разных подменю одновременно
    existing_dish = db.query(Dish).filter(Dish.submenu_id != submenu_id,
                                                Dish.title == dish_data.title).first()
    if existing_dish:
        raise HTTPException(status_code=400,
                            detail="Dish already belongs to ather submenu")

    new_dish = Dish(submenu_id=submenu_id,
                    title=dish_data.title,
                    description=dish_data.description,
                    price=dish_data.price)
    db.add(new_dish)
    db.commit()
    db.refresh(new_dish)
    return JSONResponse(
        content=
        {
            "id": str(new_dish.id),
            "title": new_dish.title,
            "description": new_dish.description,
            "price": str(round(new_dish.price, 2)),
        },
        status_code=201)


# Реализация операции Read для всех сущностей Dish
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes", response_model=DishSchema)
def read_dish_for_submenu(menu_id: str, submenu_id: str, skip: int = 0, limit: int = 10):
    db = SessionLocal()
    dishes = db.query(Dish).filter(Dish.submenu_id == submenu_id).offset(skip).limit(limit).all()
    return JSONResponse(
        content=[
        {
            "id": str(dish.id),
            "title": dish.title,
            "description": dish.description,
            "price": str(round(dish.price, 2)),
        } for dish in dishes],
        status_code=200)



# Реализация операции Read для одной сущностей Dish
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}", response_model=DishSchema)
def read_dish_for_submenu(menu_id: str, submenu_id: str, dish_id: str):
    db = SessionLocal()
    dish = db.query(Dish).filter(Dish.id == dish_id, Dish.submenu_id == submenu_id).first()

    if not dish:
        raise HTTPException(status_code=404, detail="dish not found")

    return JSONResponse(
        content=
        {
            "id": str(dish.id),
            "title": dish.title,
            "description": dish.description,
            "price": str(round(dish.price, 2)),
        },
        status_code=200)

# Реализация операции Update для сущности Dish
@app.patch("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}", response_model=DishSchema)
def update_dish(menu_id: str, submenu_id: str, dish_id: str, dish_data: DishSchemaUpdate):
    db = SessionLocal()
    updated_dish = db.query(Dish).filter(Dish.submenu_id == submenu_id,
                                         Dish.id == dish_id).first()
    if updated_dish:
        updated_dish.title = dish_data.title
        updated_dish.description = dish_data.description
        updated_dish.price = dish_data.price
        db.commit()
        db.refresh(updated_dish)

        return JSONResponse(
            content=
            {
                "id": str(updated_dish.id),
                "title": updated_dish.title,
                "description": updated_dish.description,
                "price": str(updated_dish.price),
            },
            status_code=200)


# Реализация операции Delete для сущности Dish
@app.delete("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}", response_model=DishSchema)
def delete_menu(menu_id: str, submenu_id: str, dish_id: str):
    db = SessionLocal()
    removed_dish = db.query(Dish).filter(Dish.submenu_id == submenu_id,
                                         Dish.id == dish_id).first()
    if removed_dish:
        db.delete(removed_dish)
        db.commit()
        return JSONResponse(
            content={},
            status_code=200)
