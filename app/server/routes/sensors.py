# This file adds the routes to complement the database operations in the
# database file

# The JSON Compatible Encoder from FastAPI converts the models into a format that's
# JSON compatible

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi_another_jwt_auth import AuthJWT
from app.server.routes.login import validate_access_token_rights
from datetime import timedelta, datetime


from app.server.database import (
    delete_sensor,
    retrieve_sensor_list,
    retrieve_all_sensor_lists,
    update_sensor,
    update_all_sensors,
    clear_all_sensors,
    add_sensor,
    write_sensor_status,
    return_user_role,
)
from app.server.models.sensors import (
    ErrorResponseModel,
    ResponseModel,
    SensorsSchema,
    UpdateSensorsModel,
    UpdateAllSensorsModel,
    UpdateSensorStatusModel,
)

router = APIRouter()

#location-lists for map-page
online_sensor_locations = [] #[(lat,long)]
offline_sensor_locations = [] #[(lat,long)]
    
@router.get("/update_locations", response_description="Sensor location list updated")
async def update_sensor_list( _Authorize: AuthJWT=Depends()):
    #function to update the above defined sensor location lists with the current db data
    global online_sensor_locations,offline_sensor_locations
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    online_sensor_locations = [] #reset
    offline_sensor_locations = [] #reset
    sensors = await retrieve_all_sensor_lists() #retrieve sensor data from db
    curr_time = datetime.utcnow() #get current time for online check

    for sensor in sensors:
        if sensor['status']['location_lat'] is None or sensor['status']['location_lon'] is None: #skip sensor if no location set
            continue
        #sensor is considered online if its last contact ("status_time") was less than 24h ago
        if (curr_time - datetime.utcfromtimestamp(sensor['status']['status_time'])).days == 0:
            online_sensor_locations.append([round(float(sensor['status']['location_lat']),2),round(float(sensor['status']['location_lon']),2)]) #cut after 2 decimal places!
        else:
           offline_sensor_locations.append([round(float(sensor['status']['location_lat']),2),round(float(sensor['status']['location_lon']),2)])
    return ResponseModel("", "Location list updated.")

@router.get("/get_locations", response_description="Sensor location list retrieved")
async def get_sensor_list():
    #function to deliver the sensors' locations to the map-page
    global online_sensor_locations,offline_sensor_locations
    return ResponseModel([online_sensor_locations,offline_sensor_locations], "Location lists retrieved successfully")


@router.put("/update/{_name}", response_description="Sensor status updated.")
async def update_sensor_status(_name: str, status_update: UpdateSensorStatusModel = Body(...),  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")
    
    status_update = jsonable_encoder(status_update)  # turns pydantic model to dict, which makes it JSON compatible
    updated_sensor = await write_sensor_status(_name, status_update)
    if updated_sensor == _name:
        return ResponseModel("", "Sensor status updated")
    return ErrorResponseModel(500, str(updated_sensor))


@router.get("/", response_description="Sensor lists retrieved")
async def get_all_sensor_lists( _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    sensor_lists = await retrieve_all_sensor_lists()
    if sensor_lists:
        return ResponseModel(sensor_lists, "Sensor lists retrieved successfully")
    return ResponseModel(sensor_lists, "Empty list returned")


@router.put("/all")
async def update_all_sensor_lists(update: UpdateAllSensorsModel = Body(...),  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    
    update = update.jobs
    updated_sensor_lists = await update_all_sensors(update)
    if updated_sensor_lists:
        return ResponseModel("", "Sensor lists updated")
    return ErrorResponseModel(500, "There was an error updating all sensor lists.")


@router.post("/all")
async def clear_all_sensor_lists(_Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    cleared_sensor_lists = await clear_all_sensors()
    if cleared_sensor_lists:
        return ResponseModel("", "All sensor lists cleared")
    return ErrorResponseModel(500, "There was an error clearing all sensor lists.")


# Adding a new sensor with specified name to the database, if it doesn't already exist
@router.post("/{_name}", response_description="Sensor added into the database")
async def add_new_sensor(_name: str, _Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    added_sensor = await add_sensor(_name)
    if added_sensor:
        return ResponseModel(added_sensor, "New sensor added")
    return ErrorResponseModel(409, "The sensor name already exists.") #this error-code is used in sensor_list.js, if changed change there as well


@router.get("/{_id}", response_description="Sensor list retrieved")
async def get_sensor_list(_id,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    sensor_list = await retrieve_sensor_list(_id)
    if sensor_list:
        return ResponseModel(sensor_list, "Sensor list retrieved successfully")
    return ErrorResponseModel(404, "Sensor list doesn't exist.")


@router.put("/{_id}")
async def update_sensor_list(_id: str, update: UpdateSensorsModel = Body(...),  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    update = {key: value for key, value in update.dict().items() if value is not None}
    updated_sensor_list = await update_sensor(_id, update)
    if updated_sensor_list:
        return ResponseModel("", "Sensor list with id: {} update is successful".format(_id))
    return ErrorResponseModel(500, "There was an error updating the sensor list.")


@router.delete("/{_name}", response_description="Sensor deleted from the database")
async def delete_sensor_from_db(_name: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    deleted_sensor_name = await delete_sensor(_name)
    if deleted_sensor_name:
        return ResponseModel(deleted_sensor_name, "Sensor deleted successfully")
    return ErrorResponseModel(404, "Sensor with name {0} doesn't exist".format(_name))
