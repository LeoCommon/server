from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi_another_jwt_auth import AuthJWT
from app.server.routes.login import validate_access_token_rights
import time



from app.server.database import (
    return_fixed_jobs,
    return_pending_fixed_jobs_by_sensorname,
    return_fixed_job_by_job_id,
    add_fixed_job,
    set_status,
    delete_fixed_job,
    set_sensor_status,
    return_user_role,
    check_sensorName_exists,
)
from app.server.models.FixedJobs import (
    FixedJobsSchema,
    ErrorResponseModel,
    ResponseModel,
)

router = APIRouter()


@router.get("/", response_description="Returned fixed jobs")
async def get_fixed_jobs(_Authorize: AuthJWT=Depends()):
    #permissions: user, admin, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    fixed_jobs = await return_fixed_jobs()
    if fixed_jobs is not None:
        return ResponseModel(fixed_jobs, "Retrieved fixed jobs")
    return ErrorResponseModel(500, "Could not retrieve fixed jobs")


@router.get("/{name}", response_description="Return all pending and running jobs for a given sensor_name")
async def get_fixed_jobs_by_sensorname(name: str,  _Authorize: AuthJWT=Depends()):
    #TODO: rename the router-path to "/sensor_name/{name}" for clarification. But this also needs to be adjusted in the sensors!
    #permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    fixed_jobs = await return_pending_fixed_jobs_by_sensorname(name)
    if fixed_jobs is not None:
        return ResponseModel(fixed_jobs, "Retrieved fixed jobs")
    return ErrorResponseModel(500, "Could not retrieve fixed jobs")


@router.get("/job_id/{job_id}", response_description="Return one specific job for a given job id")
async def get_fixed_jobs_by_id(job_id: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    print("execute get_fixed_jobs_by_name")
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    fixed_job = await return_fixed_job_by_job_id(job_id)
    if fixed_job is not None:
        return ResponseModel(fixed_job, "Retrieved fixed job")
    return ErrorResponseModel(500, "Could not retrieve fixed job")


@router.post("/", response_description="Created fixed job")
async def create_fixed_job(fixed_job: FixedJobsSchema = Body(...),  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    fixed_job = jsonable_encoder(fixed_job)  # converts the pydantic model to dict to make it JSON compatible
    
    #check if job starts in the past
    if fixed_job["start_time"]<int(time.time()):
        return ErrorResponseModel(500, "The job's start lies in the past.")

    fixed_job_db = await add_fixed_job(fixed_job)  # adds to db and returns new dict with inserted id in _id field
    if fixed_job_db:  # 'None' if name was not unique
        return ResponseModel(fixed_job_db, "Fixed job added successfully.")
    return ErrorResponseModel(500, "The fixed job '{}' already exists.".format(fixed_job["name"]))


@router.put("/", response_description="Status updated")
async def update_status(job_name: str, status: str,  _Authorize: AuthJWT=Depends()):
    # TODO: Where is this used? (might be a leftover from an old version)
    #permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    if status.startswith(("running", "finished", "failed")):
        updated_fixed_job = await set_status(job_name, status)
        if updated_fixed_job.matched_count > 0:
            return ResponseModel("", "Status update successful")
        return ErrorResponseModel(500, "No fixed job with name {} found".format(job_name))
    return ErrorResponseModel(500, "{} is not a valid status".format(status))


@router.put("/{sensor_name}", response_description="Status updated")
async def update_state(job_name: str, sensor_name: str, status: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, sensor
    # TODO: Is left for backward compatibility. Remove it when all sensors are updated
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    if status.startswith(("running", "finished", "failed")):
        updated_fixed_job = await set_sensor_status(job_name, sensor_name, status)
        if updated_fixed_job == "Not found":
            return ErrorResponseModel(500, "Fixed job with name {} not found.".format(job_name))
        if updated_fixed_job == "Not included":
            return ErrorResponseModel(500, "Sensor {} is not part of Fixed Job {}".format(sensor_name, job_name))
        if updated_fixed_job:
            return ResponseModel("", "Status update successful")
        return ErrorResponseModel(500, "Fixed job doesn't exist or sensor isn't part of it")
    return ErrorResponseModel(500, "{} is not a valid status".format(status))


@router.put("/update/{job_id}", response_description="Status updated")
async def update_state(job_id: str, sensor_name: str, status: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    if status.startswith(("running", "finished", "failed")):
        updated_fixed_job = await set_sensor_status(job_id, sensor_name, status)
        if updated_fixed_job == "Not found":
            return ErrorResponseModel(500, "Fixed job with name {} not found.".format(job_id))
        if updated_fixed_job == "Not included":
            return ErrorResponseModel(500, "Sensor {} is not part of Fixed Job {}".format(sensor_name, job_id))
        if updated_fixed_job:
            return ResponseModel("", "Status update successful")
        return ErrorResponseModel(500, "Fixed job doesn't exist or sensor isn't part of it")
    return ErrorResponseModel(500, "{} is not a valid status".format(status))


@router.delete("/", response_description="Removed fixed job")
async def remove_fixed_job(name: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
        
    deleted = await delete_fixed_job(name)
    if deleted:
        return ResponseModel("", "Delete fixed job successful")  # dummy for data because there is nothing to return
    return ErrorResponseModel(500, "Fixed job with name: {} does not exist".format(name))
