from pydantic import BaseModel


class MenuSchema(BaseModel):
    id : str
    title : str
    description: str


class MenuSchemaAdd(BaseModel):
    title: str
    description: str


class MenuSchemaUpdate(BaseModel):
    title: str
    description: str
