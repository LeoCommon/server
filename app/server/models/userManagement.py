from typing import Optional, List
from fastapi import HTTPException

from pydantic import BaseModel, Field



class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    role: str

class UserPwChange(BaseModel):
    password: str

def ResponseModel(data, message):
    if data is None or data == "":
        return {"message": message}
    else:
        return {
            "data": data,
            "message": message,
        }


def ErrorResponseModel(code, message):
    raise HTTPException(status_code=code, detail=message)
