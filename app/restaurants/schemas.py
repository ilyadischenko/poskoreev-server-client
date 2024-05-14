from pydantic import BaseModel, Field


class SetAdressSchema(BaseModel):
    position: str
    address: str
    kind: str = 'street'
    description: str = ''
    formattedAddress: str = ''
    entrance: str = ''
    floor: str = ''
    apartment: str = ''
    comment: str = ''


