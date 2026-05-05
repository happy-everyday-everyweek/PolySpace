from pydantic import BaseModel


class UserModel(BaseModel):
    id: str
    name: str
    email: str = ""
