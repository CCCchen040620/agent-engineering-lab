from pydantic import BaseModel


class Citation(BaseModel):
    title: str
    text: str
    path: str