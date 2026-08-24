from pydantic import BaseModel


class RoleOut(BaseModel):
    id: int
    name: str
   

    class Config:
        from_attributes = True