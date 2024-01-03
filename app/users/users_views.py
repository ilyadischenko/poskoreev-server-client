from users_models import User
from fastapi import HTTPException
import datetime
async def get_user(number : str):
    user=await User.get(number=number)
    if(user): return user
    raise HTTPException(status_code=404, detail=f"user {number} not found")

async def create_user(number : str):
    return await User.create(number=number)

async def write_code(number : str, code: int):
    current_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    user = User.filter(number=number)
    if(user): return await user.update(code=code, time_expires=current_time)
    raise HTTPException(status_code=404, detail=f"User with number {number} not found")

async def get_code(number: str):
    user = await User.get(number=number)
    if(user): return {'code': user.code, 'time_expires': user.time_expires}
    raise HTTPException(status_code=404, detail=f"User with number {number} not found")