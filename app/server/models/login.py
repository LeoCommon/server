from pydantic import BaseModel, BaseSettings
from typing import Optional
from redis import Redis
from datetime import timedelta
from fastapi import HTTPException
import secrets


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    role: str


class Settings(BaseSettings):
    authjwt_secret_key: str
    # Check for tokens in headers and cookies
    authjwt_token_location: set = {'headers','cookies'}
    # Only allow JWT cookies to be sent over https
    # authjwt_cookie_secure: bool = False

    # Disable CSRF Protection. default is True
    # does not work. If set to True, valid tokens are not validated anymore.
    authjwt_cookie_csrf_protect: bool = False

    # validity times for tokens
    user_access_token_validity = 5 * 60  # 5minutes
    user_refresh_token_validity = 2 * 60 * 60  # 2h
    sensor_access_token_validity = 24 * 60 * 60  # 24h (1 day)
    sensor_refresh_token_validity = 3 * 365 * 24 * 60 * 60  # 3*365 days
  
    class Config:
        env_file = "env/.env"


def ResponseModel(data, message):
    if data is None or data == "":
        return {"message": message}
    else:
        return {
            "data": data,
            "message": message,
        }

def ResponseTokenModel(accToken: str, refreshToken: str):
    return {
        "access_token": accToken,
        "refresh_token": refreshToken,
    }



def ErrorResponseModel(code, message):
    raise HTTPException(status_code=code, detail=message)
