from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True