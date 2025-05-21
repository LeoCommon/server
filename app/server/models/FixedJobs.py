from datetime import datetime
from typing import Optional, List, Dict
from fastapi import HTTPException

from pydantic import BaseModel, Field


# Defines the pydantic schema for fixed jobs which represents what data is expected in the request.
# The ellipsis (...) indicates that a Field is required. The field can contain validators.


class FixedJobsSchema(BaseModel):
    name: str = Field(...)
    start_time: int = Field(...)
    end_time: int = Field(...)
    command: str = Field(...)
    arguments: Dict[str, str] = Field(...)
    sensors: List[str] = Field(...)
    states: Dict[str, str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "name": "Example-1.3.2022",
                "start_time": "1646124245",
                "end_time": "1646124305",
                "command": "iridium_sniffing",
                "arguments": {"center_frequency_mhz": "1621.25", "bandwidth_khz": "1000.0"},
                "sensors": ["Berlin1", "Kaiserslautern3", "Hamburg1"],
                "states": {"Berlin1": "pending", "Kaiserslautern3": "running", "Hamburg1": "error"}
            }
        }


# can return data like inserted id or sensor ids
def ResponseModel(data, message):
    return {
        "data": data,
        "message": message,
    }


def ErrorResponseModel(code, message):
    raise HTTPException(status_code=code, detail=message)
