from typing import List

from pydantic import BaseModel


class SubMenuSchema(BaseModel):
    id : str
    title: str
    description: str
    menu_id : str


class SubMenuSchemaAdd(BaseModel):
    title: str
    description: str


class SubMenuSchemaUpdate(BaseModel):
    title: str
    description: str
