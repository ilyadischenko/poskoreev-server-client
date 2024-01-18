from pydantic import BaseModel, Field


class RefreshModels(BaseModel):
    refresh: str

