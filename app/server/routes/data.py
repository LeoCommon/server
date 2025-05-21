# This file adds the routes to complement the database operations in the
# database file

# The JSON Compatible Encoder from FastAPI converts the models into a format that's
# JSON compatible

import os
import shutil
import hashlib  # for md5hashes of files
from fileinput import filename

import aiofiles  # library for non-blocking write/read operations
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from zipfile import ZipFile
from os.path import basename
from fastapi_another_jwt_auth import AuthJWT
from app.server.routes.login import validate_access_token_rights

from app.server.database import (
    add_data,
    delete_data,
    delete_all_data_db,
    retrieve_data,
    retrieve_all_data,
    return_user_role,
    return_fixed_job_by_job_id,
)
from app.server.models.data import (
    ErrorResponseModel,
    ResponseModel,
)

router = APIRouter()
work_dir = os.getcwd()  # directory from which the script is executed, "sensor-management-system" is assumed


# adds metadata to database and file to filesystem
@router.post("/{sensor_name}/{job_name}", response_description="Sensor data added into the database")
async def add_sensor_data(sensor_name: str, job_name: str, in_file: UploadFile = File(...),  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

        
    print(in_file.content_type)
    file_content = await in_file.read()
    file_db = {"file_name": in_file.filename, "size": len(file_content)/1000.0, "file": in_file, "sensor_name": sensor_name, "job_name": job_name,}
    file_db_json = jsonable_encoder(file_db)
    new_file_db = await add_data(file_db_json)

    # save file to filesystem
    file_id = new_file_db.get('id')
    filepath = work_dir + '/app/server/file_uploads/' + in_file.filename + "_" + file_id

    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file_content)

    return ResponseModel(new_file_db, "Sensor data added successfully.")


# just_metadata is an optional query parameter that omits the actual file by default
@router.get("/", response_description="Sensor data retrieved")
async def get_all_sensor_data(_Authorize: AuthJWT=Depends()):
    #permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    data = await retrieve_all_data()
    if data:
        return ResponseModel(data, "Sensor data retrieved successfully")
    return ResponseModel(data, "Empty list returned")


# zips all files in server/file_uploads/ for the download, deletes the zip after completion
@router.get("/download", response_description="Sensor data download successful")
async def download_all(background_tasks: BackgroundTasks,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user 
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    return ErrorResponseModel(503, "Service Unavailable.")  # TODO: hotfix to pevent server crashes due to out-of-memory

    with ZipFile('app/static/download.zip', 'w') as downloadZip:
        # iterate over all saved files
        for folderName, subfolder, filenames in os.walk('app/server/file_uploads/'):
            for filename in filenames:
                if filename == ".gitkeep":
                    continue #don't add the gitkeep file
                filepath = os.path.join(folderName, filename)
                downloadZip.write(filepath, basename(filepath))
    background_tasks.add_task(remove_file, 'app/static/download.zip')  # happens after completion
    return FileResponse('app/static/download.zip', filename="download.zip")

# download one specific file
@router.get("/download/{id}", response_description="Sensor data download successful")
async def download_single(id,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")


    data = await retrieve_data(id)
    if data:
        data_file = data["file_name"]
        filepath = work_dir + '/app/server/file_uploads/' + data_file + "_" + id
        if os.path.isfile(filepath):
            return FileResponse(filepath, filename=data_file)
        return ErrorResponseModel(404, "File with id {0} doesn't exist".format(id)
        )
    return ErrorResponseModel(404, "Sensor data with id {0} doesn't exist".format(id)
    )



@router.get("/{id}", response_description="Sensor data retrieved")
async def get_sensor_data(id,  _Authorize: AuthJWT=Depends()):
    #permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    data = await retrieve_data(id)
    if data:
        return ResponseModel(data, "Sensor data retrieved successfully")
    return ErrorResponseModel(404, "Sensor data doesn't exist.")


@router.delete("/", response_description="All Sensor data deleted from the database")
async def delete_all_sensor_data(_Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")


    path = work_dir + '/app/server/file_uploads/'
    try:
        shutil.rmtree(path)
        os.mkdir(path)
        open(path+".gitkeep", 'a').close()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    deleted = await delete_all_data_db()
    if deleted:
        return ResponseModel("Deletion successful.", "All files deleted.")
    return ErrorResponseModel(500, "Internal Server Error. The Deletion did not succeed.")


# deletes the metadata entry from database and the corresponding file from the filesystem
@router.delete("/{id}", response_description="Sensor data deleted from the database")
async def delete_sensor_data(id: str,  _Authorize: AuthJWT=Depends()):
    #permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

        
    deleted_data = await delete_data(id)

    filepath = work_dir + '/app/server/file_uploads/' + deleted_data + "_" + id
    if os.path.isfile(filepath):
        os.remove(filepath)

    if deleted_data:
        return ResponseModel(
            "Sensor data with ID: {} removed".format(id), "Sensor data deleted successfully"
        )

    return ErrorResponseModel(404, "Sensor data with id {0} doesn't exist".format(id)
    )


@router.post("/upload/{sensor_name}/{job_id}", response_description="Sensor data added into the database")
async def upload_sensor_data_chunk(sensor_name: str, job_id: str, chunk_nr: int, chunks_remaining: int, chunk_md5: str, in_file: UploadFile = File(...),
                          _Authorize: AuthJWT = Depends()):
    # Hint: chunk_nr is supposed to start with 0!
    # permissions: admin, user, sensor
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin", "sensor"]):
        return ErrorResponseModel(401, "Unauthorized.")

    # write the chunk to a chunk-file
    file_content = await in_file.read()
    if not in_file.filename.__contains__("_part" + str(chunk_nr)):
        return ErrorResponseModel(422, f"Filename has to end with '_part{chunk_nr}'.")
    temp_folder = work_dir + '/app/server/file_uploads/' + 'tmp_' + job_id + '/'
    try:
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)
    except Exception:
        return ErrorResponseModel(406, f"Could not create: {temp_folder}")
    filepath = temp_folder + in_file.filename
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file_content)

    # verify the chunk is correct
    md5hash = get_md5_hash(filepath)
    print(f"MD5({filepath})={md5hash}")
    if md5hash != chunk_md5:
        remove_file(filepath)  # cleanup: delete the wrong file
        return ErrorResponseModel(409, "Wrong checksum.")

    if chunks_remaining > 0:
        # wait for more chunks
        # TODO: What happens if the last chunk is never send? You fill the disk with garbage. Implement a auto-delete
        #  after n seconds. (At this stage all devices are authenticated, so it is not critical.)
        return ResponseModel(None, "Chunk uploaded.")

    # Last chunk received. (1) combine the chunks, (2) insert file-ref to DB, (3) store on disk, (4) cleanup tmp-storage
    full_file = bytearray()
    raw_name = in_file.filename[:in_file.filename.rindex("_part")]
    for i in range(chunk_nr+1):
        chunk_name = temp_folder + raw_name + "_part" + str(i)
        if not os.path.exists(chunk_name):
            return ErrorResponseModel(416, f"Missing file-part: {raw_name}_part{i}")
        with open(chunk_name, "rb") as f:
            chunk_data = f.read()
            full_file.extend(chunk_data)

    # insert file-ref to DB
    job = await return_fixed_job_by_job_id(job_id)
    job_name = job["name"]
    file_db = {"file_name": raw_name, "size": len(full_file) / 1000.0, "file": None,
               "sensor_name": sensor_name, "job_name": job_name, }
    file_db_json = jsonable_encoder(file_db)
    new_file_db = await add_data(file_db_json)
    file_id = new_file_db.get('id')

    # save file to filesystem
    filepath = work_dir + '/app/server/file_uploads/' + raw_name + "_" + file_id
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(full_file)

    # cleanup tmp-storage
    for file in os.listdir(temp_folder):
        print(f"delete: {file}")
        remove_file(os.path.join(temp_folder, file))
    shutil.rmtree(temp_folder)

    return ResponseModel(new_file_db, "Data uploaded successfully.")


def remove_file(path: str) -> None:
    os.unlink(path)


def get_md5_hash(file_name: str) -> str:
    # src: https://stackoverflow.com/questions/16874598/how-to-calculate-the-md5-checksum-of-a-file-in-python
    # Read 8192 (or 2¹³) bytes of a file at a time instead of all at once with f.read() to use less memory.
    with open(file_name, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    return file_hash.hexdigest()

