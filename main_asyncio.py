from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from config import DATABASE_URL_ASYNCIO
from models import Menu, SubMenu, Dish
from schemas.menu import MenuSchema, MenuSchemaAdd, MenuSchemaUpdate
from schemas.submenu import SubMenuSchema, SubMenuSchemaAdd, \
    SubMenuSchemaUpdate
from schemas.dish import DishSchema, DishSchemaAdd, DishSchemaUpdate

app = FastAPI()

# Создаем соединение с базой данных
async_engine = create_async_engine(DATABASE_URL_ASYNCIO)

async_session = sessionmaker(bind=async_engine, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# Реализация операции Create для сущности Menu
@app.post("/api/v1/menus/", response_model=MenuSchema)
async def create_menu(menu_data: MenuSchemaAdd,
                      session: AsyncSession = Depends(get_session)):
    """
        Добавляет новую запись в БД в таблице Menu.

        Parameters:
            menu_data (MenuSchemaAdd):  Данные для добавления меню.
            session (AsyncSession): Асинхронная сессия с базой данных.

        Returns:
            JSONResponse: Ответ с информацией о меню.
    """
    new_menu = Menu(title=menu_data.title, description=menu_data.description)
    session.add(new_menu)
    await session.commit()
    await session.refresh(new_menu)

    return JSONResponse(
        content={
            "id": str(new_menu.id),
            "title": new_menu.title,
            "description": new_menu.description
        },
        status_code=201)


# Реализация операции Read для всех сущностей Menu
@app.get("/api/v1/menus/", response_model=MenuSchema)
async def read_menus(skip: int = 0, limit: int = 10,
                     session: AsyncSession = Depends(get_session)):
    """
    Получает все записи из БД из таблицы Menu.

    Parameters:
        skip (int): Число записей, которое следует пропустить перед возвратом
        limit (int): Максимальное количество записей, которые следует вернуть.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ с информацией о меню.
    """
    query = select(Menu)
    menus = await session.execute(query.offset(skip).limit(limit))

    response_data = []
    for menu in menus.scalars():
        submenus_count = await session.execute(
            select(func.count(SubMenu.id)).filter(
                SubMenu.menu_id == menu.id))
        submenus_count = submenus_count.scalar()

        dishes_count = await session.execute(
            select(func.count(Dish.id)).join(SubMenu).filter(
                SubMenu.menu_id == menu.id))
        dishes_count = dishes_count.scalar()

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
async def read_one_menu(menu_id: str,
                        session: AsyncSession = Depends(get_session)):
    """
    Получает запись из БД из таблицы Menu по указанному идентификатору.

    Parameters:
        menu_id (str): Идентификатор меню.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ с информацией о меню.

    Raises:
        HTTPException: Если меню с указанным идентификатором
        не найдено в базе данных.
    """
    query = select(Menu).filter(Menu.id == menu_id)
    menu = await session.execute(query)
    menu = menu.scalar_one_or_none()

    # Обрабатываем случай, в котором меню еще не создано
    if not menu:
        raise HTTPException(status_code=404, detail="menu not found")

    # Определяем количество подменю в меню
    submenus_count = await session.execute(
        select(func.count(SubMenu.id)).filter(
            SubMenu.menu_id == menu_id))
    submenus_count = submenus_count.scalar()

    # Определяем количество блюд в меню
    subquery = select(func.count(Dish.id)).join(SubMenu).filter(
        SubMenu.menu_id == menu_id).subquery()
    dishes_count = await session.execute(select(func.sum(subquery)))
    dishes_count = dishes_count.scalar()

    return JSONResponse(
        content={
            "id": str(menu.id),
            "title": menu.title,
            "description": menu.description,
            "submenus_count": int(submenus_count),
            "dishes_count": int(dishes_count),
        },
        status_code=200)


# Реализация операции Update для сущности Menu
@app.patch("/api/v1/menus/{menu_id}", response_model=MenuSchema)
async def update_menu(menu_id: str, menu_data: MenuSchemaUpdate,
                      session: AsyncSession = Depends(get_session)):
    """
    Обновляет запись в БД в таблице Menu по указанному идентификатору.

    Parameters:
        menu_id (str): Идентификатор меню, которое необходимо обновить.
        menu_data (MenuSchemaUpdate): Данные для обновления меню.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ с информацией о меню.

    Raises:
        HTTPException: Если меню с указанным идентификатором
        не найдено в базе данных.
    """
    query = select(Menu).filter(Menu.id == menu_id)
    updated_menu = await session.execute(query)
    updated_menu = updated_menu.scalar_one_or_none()

    if updated_menu:
        updated_menu.title = menu_data.title
        updated_menu.description = menu_data.description
        await session.commit()
        await session.refresh(updated_menu)

        return JSONResponse(
            content={
                "id": str(updated_menu.id),
                "title": updated_menu.title,
                "description": updated_menu.description,
            },
            status_code=200)

    raise HTTPException(status_code=404, detail="menu not found")


# Реализация операции Delete для сущности Menu
@app.delete("/api/v1/menus/{menu_id}", response_model=MenuSchema)
async def delete_menu(menu_id: str,
                      session: AsyncSession = Depends(get_session)):
    """
    Удаляет запись из БД из таблицы Menu по указанному идентификатору.

    Parameters:
        menu_id (str): Идентификатор меню, которое необходимо удалить.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns: JSONResponse: Пустой JSON-ответ с кодом 200 в случае успешного
    удаления.

    Raises:
        HTTPException: Если меню с указанным идентификатором не найдено в
        базе данных.
    """
    query = select(Menu).filter(Menu.id == menu_id)
    removed_menu = await session.execute(query)
    removed_menu = removed_menu.scalar_one_or_none()

    if removed_menu:
        await session.delete(removed_menu)
        await session.commit()

        return JSONResponse(content={}, status_code=200)

    raise HTTPException(status_code=404, detail="menu not found")


# Реализация операции Create для сущности Submenu
@app.post("/api/v1/menus/{menu_id}/submenus", response_model=SubMenuSchema)
async def create_submenu_for_menu(menu_id: str, submenu_data: SubMenuSchemaAdd,
                                  session: AsyncSession = Depends(
                                      get_session)):
    """
    Добавляет запись в БД в таблице SubMenu для указанного меню по id.

    Parameters:
        menu_id (str): Идентификатор меню, к которому добавляется подменю.
        submenu_data (SubMenuSchemaAdd): Данные для создания нового подменю.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: JSON-ответ с информацией о созданном подменю и кодом 201.

    Raises:
        HTTPException: Если меню с указанным идентификатором не найдено в
        базе данных или если подменю с указанным заголовком уже принадлежит
        другому меню.
    """
    query = select(Menu).filter(Menu.id == menu_id)
    menu = await session.execute(query)

    if not menu.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="menu not found")

    # Проверка по критерию
    # невозможности нахождения подменю в разных меню одновременно
    query = select(SubMenu).filter(SubMenu.menu_id != menu_id,
                                   SubMenu.title == submenu_data.title)
    existing_submenu = await session.execute(query)

    if existing_submenu.scalar_one_or_none():
        raise HTTPException(status_code=400,
                            detail="Submenu already belongs to ather menu")

    # При прохождении всех проверок
    # создается новый объект и добавляется в таблицу
    new_submenu = SubMenu(menu_id=menu_id,
                          title=submenu_data.title,
                          description=submenu_data.description)

    session.add(new_submenu)
    await session.commit()
    await session.refresh(new_submenu)
    return JSONResponse(
        content={
            "id": str(new_submenu.id),
            "title": new_submenu.title,
            "description": new_submenu.description
        },
        status_code=201)


# Реализация операции Read для всех сущности Submenu
@app.get("/api/v1/menus/{menu_id}/submenus", response_model=SubMenuSchema)
async def read_submenus_for_menu(menu_id: str, skip: int = 0, limit: int = 10,
                                 session: AsyncSession = Depends(get_session)):
    """
    Получает все записи из БД из таблицы SubMenu для указанного меню по его id.

    Parameters:
       menu_id (str): Идентификатор меню, для которого нужно получить список подменю.
       skip (int, optional): Количество записей, которое нужно пропустить.
       limit (int, optional): Максимальное количество записей для возврата.
       session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
       JSONResponse: JSON-ответ с информацией о подменю и кодом 200.
    """
    query = select(SubMenu).filter(SubMenu.menu_id == menu_id).offset(
        skip).limit(limit)
    submenus = await session.execute(query)

    response_data = []
    for submenu in submenus.scalars():
        query = select(func.count(Dish.id)).filter(
            Dish.submenu_id == submenu.id)
        dishes_count = await session.execute(query)
        dishes_count = dishes_count.scalar()

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
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}",
         response_model=SubMenuSchema)
async def read_one_submenu_for_menu(menu_id: str, submenu_id: str,
                                    session: AsyncSession = Depends(
                                        get_session)):
    """
    Получает одну запись о конкретном подменю из БД из таблицы SubMenu
    для указанного меню по его id.

    Parameters:
        menu_id (str): Идентификатор меню, к которому принадлежит подменю.
        submenu_id (str): Идентификатор подменю, которое нужно получить.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: JSON-ответ с информацией о подменю и кодом 200.

    Raises:
        HTTPException: Если меню или подменю с указанными идентификаторами не
        найдены в базе данных.
    """
    query = select(SubMenu).filter(SubMenu.menu_id == menu_id,
                                   SubMenu.id == submenu_id)
    submenu = await session.execute(query)
    submenu = submenu.scalar_one_or_none()

    if not submenu:
        raise HTTPException(status_code=404, detail="submenu not found")

    query = select(func.count(Dish.id)).filter(Dish.submenu_id == submenu.id)
    dishes_count = await session.execute(query)
    dishes_count = dishes_count.scalar()

    return JSONResponse(
        content={
            "id": str(submenu.id),
            "title": submenu.title,
            "description": submenu.description,
            "dishes_count": int(dishes_count),
        },
        status_code=200)


# Реализация операции Update для сущности Submenu
@app.patch("/api/v1/menus/{menu_id}/submenus/{submenu_id}",
           response_model=SubMenuSchema)
async def update_submenu(menu_id: str, submenu_id: str,
                         submenu_data: SubMenuSchemaUpdate,
                         session: AsyncSession = Depends(get_session)):
    """
    Обновляет запись в БД в таблице SubMenu по указанному идентификатору
    подменю для указанного меню.

    Parameters:
       menu_id (str): Идентификатор меню, к которому принадлежит подменю.
       submenu_id (str): Идентификатор подменю, которое нужно обновить.
       submenu_data (SubMenuSchemaUpdate): данные для обновления записи.
       session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
       JSONResponse: JSON-ответ с обновленной информацией о подменю и
       кодом 200.

    Raises:
       HTTPException: Если меню или подменю с указанными идентификаторами не
       найдены в базе данных.
    """
    query = select(SubMenu).filter(SubMenu.menu_id == menu_id,
                                   SubMenu.id == submenu_id)
    updated_submenu = await session.execute(query)
    updated_submenu = updated_submenu.scalar_one_or_none()

    if updated_submenu:
        updated_submenu.title = submenu_data.title
        updated_submenu.description = submenu_data.description
        await session.commit()
        await session.refresh(updated_submenu)

        return JSONResponse(
            content={
                "id": str(updated_submenu.id),
                "title": updated_submenu.title,
                "description": updated_submenu.description,
            },
            status_code=200)


# Реализация операции Delete для сущности Submenu
@app.delete("/api/v1/menus/{menu_id}/submenus/{submenu_id}",
            response_model=SubMenuSchema)
async def delete_submenu(menu_id: str, submenu_id: str,
                         session: AsyncSession = Depends(get_session)):
    """
    Удаляет запись из БД из таблицы SubMenu по указанному идентификатору
    подменю для указанного меню.

    Parameters:
        menu_id (str): Идентификатор меню, к которому принадлежит подменю.
        submenu_id (str): Идентификатор подменю, которое нужно удалить.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Пустой JSON-ответ и код 200 в случае успешного удаления.

    Raises:
        HTTPException: Если меню или подменю с указанными идентификаторами
        не найдены в базе данных.
    """
    query = select(SubMenu).filter(SubMenu.menu_id == menu_id,
                                   SubMenu.id == submenu_id)
    removed_submenu = await session.execute(query)
    removed_submenu = removed_submenu.scalar_one_or_none()

    if removed_submenu:
        await session.delete(removed_submenu)
        await session.commit()

        return JSONResponse(
            content={},
            status_code=200)


# Реализация операции Create для сущности Dish
@app.post("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes",
          response_model=DishSchema)
async def create_dish_for_submenu(menu_id: str, submenu_id: str,
                                  dish_data: DishSchemaAdd,
                                  session: AsyncSession = Depends(
                                      get_session)):
    """
    Получает список блюд для указанного подменю.

    Parameters:
        menu_id (str): Идентификатор меню, к которому относится подменю.
        submenu_id (str): Идентификатор подменю, для которого получается список блюд.
        skip (int): Количество пропускаемых блюд.
        limit (int): Максимальное количество блюд в списке.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ со списком блюд для указанного подменю.
    """
    query = select(SubMenu).filter(SubMenu.menu_id == menu_id,
                                   SubMenu.id == submenu_id)
    # Проверка наличия подменю в которое добавляется блюдо
    submenu = await session.execute(query)

    if not submenu.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Submenu not found")

    # Проверка по критерию
    # невозможности нахождения блюда в разных подменю одновременно
    query = select(Dish).filter(Dish.submenu_id != submenu_id,
                                Dish.title == dish_data.title)
    existing_dish = await session.execute(query)

    if existing_dish.scalar_one_or_none():
        raise HTTPException(status_code=400,
                            detail="Dish already belongs to ather submenu")

    new_dish = Dish(submenu_id=submenu_id,
                    title=dish_data.title,
                    description=dish_data.description,
                    price=dish_data.price,
                    )

    session.add(new_dish)
    await session.commit()
    await session.refresh(new_dish)

    return JSONResponse(
        content={
            "id": str(new_dish.id),
            "title": new_dish.title,
            "description": new_dish.description,
            "price": str(round(new_dish.price, 2)),
        },
        status_code=201)


# Реализация операции Read для всех сущностей Dish
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes",
         response_model=DishSchema)
async def read_dishes_for_submenu(submenu_id: str, skip: int = 0,
                                  limit: int = 10,
                                  session: AsyncSession = Depends(
                                      get_session)):
    """
    Получает список блюд для указанного подменю.

    Parameters:
       menu_id (str): Идентификатор меню.
       submenu_id (str): Идентификатор подменю.
       skip (int): Количество пропускаемых блюд.
       limit (int): Максимальное количество возвращаемых блюд.
       session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
       JSONResponse: Список блюд для указанного подменю.
    """
    query = select(Dish).filter(Dish.submenu_id == submenu_id).offset(
        skip).limit(limit)
    dishes = await session.execute(query)
    dishes = dishes.scalars()
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
@app.get("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}",
         response_model=DishSchema)
async def read_dish_for_submenu(submenu_id: str, dish_id: str,
                                session: AsyncSession = Depends(get_session)):
    """
    Получает информацию о конкретном блюде для указанного подменю.

    Parameters:
        submenu_id (str): Идентификатор подменю, к которому относится блюдо.
        dish_id (str): Идентификатор блюда.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ с информацией о блюде.

    Raises:
        HTTPException: Если блюдо не найдено.
    """
    query = select(Dish).filter(Dish.id == dish_id,
                                Dish.submenu_id == submenu_id)
    dish = await session.execute(query)
    dish = dish.scalar_one_or_none()

    if not dish:
        raise HTTPException(status_code=404, detail="dish not found")

    return JSONResponse(
        content={
            "id": str(dish.id),
            "title": dish.title,
            "description": dish.description,
            "price": str(round(dish.price, 2)),
        },
        status_code=200)


# Реализация операции Update для сущности Dish
@app.patch("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}",
           response_model=DishSchema)
async def update_dish(submenu_id: str, dish_id: str,
                      dish_data: DishSchemaUpdate,
                      session: AsyncSession = Depends(get_session)):
    """
    Обновляет информацию о блюде в указанном подменю.

    Parameters:
        submenu_id (str): Идентификатор подменю, к которому относится блюдо.
        dish_id (str): Идентификатор блюда, которое требуется обновить.
        dish_data (DishSchemaUpdate): Обновленные данные для блюда.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Ответ с информацией об обновленном блюде.
    """
    query = select(Dish).filter(Dish.submenu_id == submenu_id,
                                Dish.id == dish_id)
    updated_dish = await session.execute(query)
    updated_dish = updated_dish.scalar_one_or_none()

    if updated_dish:
        updated_dish.title = dish_data.title
        updated_dish.description = dish_data.description
        updated_dish.price = dish_data.price
        await session.commit()
        await session.refresh(updated_dish)

        return JSONResponse(
            content={
                "id": str(updated_dish.id),
                "title": updated_dish.title,
                "description": updated_dish.description,
                "price": str(updated_dish.price),
            },
            status_code=200)


# Реализация операции Delete для сущности Dish
@app.delete("/api/v1/menus/{menu_id}/submenus/{submenu_id}/dishes/{dish_id}",
            response_model=DishSchema)
async def delete_dish(submenu_id: str, dish_id: str,
                      session: AsyncSession = Depends(get_session)):
    """
    Удаляет указанное блюдо из подменю.

    Parameters:
        menu_id (str): Идентификатор меню.
        submenu_id (str): Идентификатор подменю.
        dish_id (str): Идентификатор удаляемого блюда.
        session (AsyncSession): Асинхронная сессия с базой данных.

    Returns:
        JSONResponse: Пустой ответ, если блюдо успешно удалено.

    Raises:
        HTTPException: Если указанное блюдо не найдено в подменю.
    """
    query = select(Dish).filter(Dish.submenu_id == submenu_id,
                                Dish.id == dish_id)
    removed_dish = await session.execute(query)
    removed_dish = removed_dish.scalar_one_or_none()

    if removed_dish:
        await session.delete(removed_dish)
        await session.commit()

        return JSONResponse(
            content={},
            status_code=200)
