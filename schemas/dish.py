from pydantic import BaseModel, Field


class DishSchema(BaseModel):
    id: str
    title: str
    description: str
    price: float = Field(ge=0.0)
    submenu_id: str


class DishSchemaAdd(BaseModel):
    title: str
    description: str
    price: float = Field(ge=0)


class DishSchemaUpdate(BaseModel):
    title: str
    description: str
    price: float = Field(ge=0)
