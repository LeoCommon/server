from typing import Optional, List
from fastapi import HTTPException

from pydantic import BaseModel, Field


# Defines the pydantic schema for sensor lists which represents what data a request expects.
# The ellipsis (...) indicates that a Field is required. The field can contain validators.


class UpdateSensorStatusModel(BaseModel):
    status_time: int
    location_lon: str
    location_lat: str
    os_version: str
    temperature_celsius: float
    LTE: str
    WiFi: str
    Ethernet: str

    class Config:
        schema_extra = {
            "example": {
                "status_time": "1646124245",
                "location_lat": "49.5534",
                "location_lon": "8.23865",
                "os_version": "1.0a",
                "temperature_celsius": "0.0",
                "LTE": "online",
                "WiFi": "offline",
                "Ethernet": "offline"
            }
        }


class SensorsSchema(BaseModel):
    sensor_name: str = Field(...)
    jobs: List[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "sensor_name": "sensor1",
                "jobs": ["job1", "job2"]
            }
        }


class UpdateSensorsModel(BaseModel):
    sensor_name: Optional[str]
    jobs: Optional[List[str]]

    class Config:
        schema_extra = {
            "example": {
                "sensor_name": "sensor1",
                "jobs": ["job1", "job2", "job3"]
            }
        }


class UpdateAllSensorsModel(BaseModel):
    jobs: List[str]

    class Config:
        schema_extra = {
            "example": {
                "jobs": ["job1", "job2", "job3"]
            }
        }


# can return data like inserted id or a job list
def ResponseModel(data, message):
    return {
        "data": data,
        "message": message,
    }


def ErrorResponseModel(code, message):
    raise HTTPException(status_code=code, detail=message)
