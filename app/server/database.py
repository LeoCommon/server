# This file is responsible for the database connection and queries using Motor
# The Motor methods are similar to the MongoDB methods they execute, however the MongoDB documentation is more detailed:
# MongoDB collection methods: https://docs.mongodb.com/manual/reference/method/js-collection/
# Motor collection methods: https://motor.readthedocs.io/en/stable/api-tornado/motor_collection.html
# The only difference is that MongoDB methods use lowerCamelCase while Motor methods use underscore,
# e.g. findOne() becomes find_one() and MongoDB operators are encapsulated in quotation marks, plenty of examples below

# Motor is an asynchronous Python driver for MongoDB
import motor.motor_asyncio
import pymongo
from bson.objectid import ObjectId
import bcrypt
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection

# connection details
MONGO_DETAILS = "mongodb://localhost:27017"

# create a client with the connection details
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

# reference the database called "sensors"
database = client.sensors

# reference collections (akin to tables) in the database
data_collection = database.get_collection("data_collection")
sensors_collection = database.get_collection("sensors_collection")
fixed_jobs_collection = database.get_collection("fixed_jobs")
user_collection = database.get_collection("users")
token_blacklist = database.get_collection("access_token_blacklist")
token_whitelist = database.get_collection("refresh_token_whitelist")

# sensor.status default-dict.
sensor_default_status_dict = {
    "status_time": 0,
    "location_lat": None,
    "location_lon": None,
    "os_version": None,
    "temperature_celsius": None,
    "LTE": "offline",
    "WiFi": "offline",
    "Ethernet": "offline"
}

user_default_dict = {
    "email": "",
    "username": "",
    "hashed_password": bytes,
    "role": "",
    "creation_date": 0,
    "owned_sensors": [],
    "scheduled_jobs": [],
    "online_status": [[0,0]],
    "public_rsa_key": "",
}

# helper functions to parse results from database query into Python dict

def data_helper(data) -> dict:
    return {
        "id": str(data["_id"]),
        "file_name": data["file_name"],
        "size": data["size"],
        "sensor_name": data["sensor_name"],
        "job_name": data["job_name"],
    }


def sensor_helper(sensor) -> dict:
    temp_status = sensor_default_status_dict.copy()
    for key in sensor["status"].keys():
        temp_status[key] = sensor["status"][key]
    return {
        "id": str(sensor["_id"]),
        "sensor_name": sensor["sensor_name"],
        "jobs": sensor["jobs"],
        "status": temp_status
    }


def fixed_jobs_helper(fixed_job) -> dict:
    return {
        "id": str(fixed_job["_id"]),
        "name": fixed_job["name"],
        "start_time": fixed_job["start_time"],
        "end_time": fixed_job["end_time"],
        "command": fixed_job["command"],
        "arguments": fixed_job["arguments"],
        "sensors": fixed_job["sensors"],
        "status": fixed_job["status"],
        "states": fixed_job["states"],
    }


def refresh_token_helper(ref_token) -> dict:
    return {
        "jti": str(ref_token["jti"]),
        "sub": ref_token["sub"],
        "exp": ref_token["expire"],
        "time_added": ref_token["time_added"],
        "sibling_jti": ref_token["sibling_jti"],
        "sibling_exp": ref_token["sibling_exp"],
    }


def online_status_helper(history) -> list:
    online_list = []
    # list of pairs with start- and (rough) end-time of an user activity
    for elem in list(history):
        el1, el2 = elem
        online_list.append((el1, el2))
    return online_list


def user_helper(db_user) -> dict:
    # don't touch the password
    user_dict = {}
    user_dict["id"] = str(db_user["_id"])
    user_dict["email"] = str(db_user["email"])
    user_dict["username"] = str(db_user["username"])
    user_dict["role"] = str(db_user["role"])
    if "creation_date" in db_user.keys():
        user_dict["creation_date"] = int(db_user["creation_date"])
    else:
        user_dict["creation_date"] = 0
    if "online_status" in db_user.keys():
        user_dict["online_status"] = online_status_helper(db_user["online_status"])
    else:
        user_dict["online_status"] = online_status_helper([(0, 1)])
    if "owned_sensors" in db_user.keys():
        user_dict["owned_sensors"] = db_user["owned_sensors"]
    else:
        user_dict["owned_sensors"] = []
    if "scheduled_jobs" in db_user.keys():
        user_dict["scheduled_jobs"] = db_user["scheduled_jobs"]
    else:
        user_dict["scheduled_jobs"] = []
    if "public_rsa_key" in db_user.keys():
        user_dict["public_rsa_key"] = db_user["public_rsa_key"]
    else:
        user_dict["public_rsa_key"] = ""
    return user_dict


# security helper functions to check inputs

def is_number(in_string) -> bool:
    return in_string.isdecimal()


def uses_allowed_characters(in_string) -> bool:
    in_string = str(in_string)
    if len(in_string) == 0:
        return False
    if not in_string.isascii():
        return False
    for char in in_string:
        allowed_chars = lambda char: char.isalnum() or char in ['-', '_', '.', ':', '+', '(', ')', '@', '/']
        if not allowed_chars(char):
            return False
    return True


def is_allowed_user_role(in_role) -> bool:
    allowed_roles = ["user", "admin", "sensor"]
    if in_role in allowed_roles:
        return True
    else:
        return False


# CRUD operations: async create, read, update and delete in the database via motor

# -----------------------------------------
# ----------- DATA METHODS ----------------
# -----------------------------------------

# Retrieve entirety of sensor data
async def retrieve_all_data():
    all_data = []
    all_data_cursor = data_collection.find()
    # convert cursor to list, iterate items through data_helper
    for data in await all_data_cursor.to_list(length=None):
        all_data.append(data_helper(data))
    return all_data


# Add new sensor data dict to database
async def add_data(sensor_data: dict) -> dict:
    data = await data_collection.insert_one(sensor_data)
    new_data = await data_collection.find_one({"_id": data.inserted_id})
    return data_helper(new_data)


# Retrieve sensor data with matching ID
async def retrieve_data(_id: str) -> dict:
    data = await data_collection.find_one({"_id": ObjectId(_id)})
    if data:
        return data_helper(data)


# Delete data from database
async def delete_data(_id: str):
    data = await data_collection.find_one({"_id": ObjectId(_id)})
    name = data["file_name"]
    if data:
        await data_collection.delete_one({"_id": ObjectId(_id)})
        return name


# Delete all data from db
async def delete_all_data_db():
    result = await data_collection.delete_many({})
    if result:
        return True
    return False


# -----------------------------------------
# ----------- SENSOR LIST METHODS ------------
# -----------------------------------------

# Retrieve all job lists
async def retrieve_all_sensor_lists():
    all_sensors = []
    all_sensors_cursor = sensors_collection.find()
    for sensor in await all_sensors_cursor.to_list(length=None):
        all_sensors.append(sensor_helper(sensor))
    return all_sensors


# Retrieve job list with matching ID
async def retrieve_sensor_list(_id: str) -> dict:
    sensor = await sensors_collection.find_one({"_id": ObjectId(_id)})
    if sensor:
        return sensor_helper(sensor)


# Update job list entry with matching ID
async def update_sensor(_id: str, jobs: dict):
    if len(jobs) < 1:
        return False

    # check if the pointers are valid, if a pending fixed job isn't found the operation fails
    for job in jobs["jobs"]:
        fixed_job = await fixed_jobs_collection.find_one({"name": job, "status": "pending"})
        if not fixed_job:
            return False

    # check if sensor exists and update it
    sensor_db = await sensors_collection.find_one({"_id": ObjectId(_id)})
    if sensor_db:
        sensor_name = sensor_db["sensor_name"]
        updated_sensors = await sensors_collection.update_one({"_id": ObjectId(_id)}, {"$set": jobs})

        # special case: update job list is empty - implies 'clear jobs'.
        # Sensor has to be removed from all pending fixed jobs
        if not jobs["jobs"]:
            await fixed_jobs_collection.update_many(
                {"status": "pending"},
                {"$pull": {"sensors": sensor_name}}
            )
            await fixed_jobs_collection.update_many(
                {"status": "pending"},
                {"$unset": {"states." + sensor_name: ""}}
            )
        else:
            # add sensor pointer to all pending fixed jobs that were added
            await fixed_jobs_collection.update_many(
                {"name": {"$in": jobs["jobs"]}, "status": "pending"},
                {"$addToSet": {"sensors": sensor_name}}
            )

            # add pending state for the sensor to all jobs that were added
            await fixed_jobs_collection.update_many(
                {"name": {"$in": jobs["jobs"]}, "status": "pending"},
                {"$set": {"states." + sensor_name: "pending"}}
            )

        if updated_sensors:
            return True
        return False


# Update all job lists by adding the new jobs
async def update_all_sensors(jobs: [str]):
    if len(jobs) < 1:
        return False
    # check if the pointers are valid, if a pending fixed job isn't found the operation fails
    for job in jobs:
        fixed_job = await fixed_jobs_collection.find_one({"name": job, "status": "pending"})
        if not fixed_job:
            return False
    # push each of the input jobs to all collection items into the "sensors" array
    updated_sensors = await sensors_collection.update_many(
        {},
        {"$push": {"jobs": {"$each": jobs}}}
    )

    # update fixed jobs with new sensor pointers:
    sensors_cursor = sensors_collection.find()  # cursor containing all sensors
    sensor_names = []
    # compile list of all sensor_names
    for sensor in await sensors_cursor.to_list(length=None):
        sensor_names.append(sensor["sensor_name"])
    # add sensor_names to added fixed jobs
    await fixed_jobs_collection.update_many(
        {"name": {"$in": jobs}, "status": "pending"},
        {"$addToSet": {"sensors": {"$each": sensor_names}}}
    )
    # add pending state for each sensor to states
    for sensor in sensor_names:
        await fixed_jobs_collection.update_many(
            {"name": {"$in": jobs}, "status": "pending"},
            {"$set": {"states." + sensor: "pending"}}
        )

    if updated_sensors:
        return True
    return False


# Clear all sensor lists
async def clear_all_sensors():
    cleared_jobs = await sensors_collection.update_many(
        {},
        {"$set": {"jobs": []}}
    )
    # clear sensor pointers of all pending fixed jobs and clear all states
    await fixed_jobs_collection.update_many(
        {"status": "pending"},
        {"$set": {"sensors": [], "states": {}}}
    )
    if cleared_jobs:
        return True
    return False


# Add new sensor with empty job list to database, if its name doesn't already exist
async def write_sensor_status(name: str, new_status: dict):
    if not uses_allowed_characters(name):
        return "invalid sensor name"
    sensor_to_update = await sensors_collection.find_one({"sensor_name": name})
    if sensor_to_update:
        # ensure that only valid keys and states enter the db
        status_update = sensor_default_status_dict.copy()
        for key in new_status.keys():
            if uses_allowed_characters(key) and key in status_update.keys() and uses_allowed_characters(
                    new_status[key]):
                status_update[key] = new_status[key]
            else:
                return "invalid status-argument: " + str(key) + ":" + str(new_status[key])
        updated_sensors = await sensors_collection.update_one({"sensor_name": name},
                                                              {"$set": {"status": status_update}})
        if updated_sensors:
            return name
    return "sensor not found"


# Add new sensor with empty job list to database, if its name doesn't already exist
async def add_sensor(_name: str):
    already_exists = await sensors_collection.find_one({"sensor_name": _name})
    if not already_exists:
        added_sensor = await sensors_collection.insert_one(
            {
                "sensor_name": _name,
                "jobs": [],
                "status": sensor_default_status_dict
            })
        if added_sensor:
            return str(added_sensor.inserted_id)  # ObjectId() to String
    return None


# Delete sensor list from database
async def delete_sensor(_name: str):
    deleted_sensor = await sensors_collection.find_one({"sensor_name": _name})
    if deleted_sensor:
        db_id = deleted_sensor["_id"]
        await sensors_collection.delete_one({"_id": db_id})
        # remove the sensor from all pending fixed jobs
        fixed_jobs_collection.update_many(
            {"status": "pending"},
            {"$pull": {"sensors": deleted_sensor["sensor_name"]}}
        )
        # remove sensor state from all pending fixed jobs
        fixed_jobs_collection.update_many(
            {"status": "pending"},
            {"$unset": {deleted_sensor["sensor_name"]: ""}}
        )
        return str(db_id)
    return None


# Check if sensor with sensorName exists
async def check_sensorName_exists(sensorName: str):
    does_exist = await sensors_collection.find_one({"sensor_name": sensorName})
    if does_exist:
        return True
    else:
        return False


# Check if sensor with densorID exists
async def check_sensorID_exists(sensorID: str):
    does_exist = await sensors_collection.find_one({"_id": ObjectId(sensorID)})
    if does_exist:
        return True
    else:
        return False


# -----------------------------------------
# ----------- FIXED JOB METHODS -----------
# -----------------------------------------

# add fixed job to fixed_jobs collection, add job pointer to the specified sensors,
# return dict with inserted id in _id field if successful
async def add_fixed_job(fixed_job: dict):
    fixed_job["status"] = "pending"  # newly created fixed jobs initially have status: pending
    fixed_job["states"] = {}  # initialize empty document (key-value pairs) for the individual sensor statuses
    # only execute when job name is unique
    already_exists = await fixed_jobs_collection.find_one({"name": fixed_job["name"]})
    if not already_exists:
        result = await fixed_jobs_collection.insert_one(fixed_job)  # returns the inserted id on success
        fixed_job_db = await fixed_jobs_collection.find_one({"_id": result.inserted_id})  # fetch the document by the id
        return fixed_jobs_helper(fixed_job_db)
    return None


# set status of a job to "running", "finished" or "failed". Invalid values get caught before this method is called.
async def set_status(name: str, status: str):
    # set the status of the first document matching 'name' to 'status'
    updated_job = await fixed_jobs_collection.update_one({"name": name}, {"$set": {"status": status}})
    # returns a document with matchedCount, modifiedCount, upsertedId, acknowledged. See MongoDB docs for updateOne().
    return updated_job


# set state of a sensor within a fixed job (running, finished, failed)
# set status of a fixed job depending on sensor states
async def set_sensor_status(job_id: str, sensor: str, status: str):
    # TODO: remove backwards compatibility when sensors are all updated: check if job_id is maybe a job_name
    maybe_job = await fixed_jobs_collection.find_one({"name": job_id})
    if maybe_job:
        job_id = maybe_job["_id"]

    update_job = await fixed_jobs_collection.find_one({"_id": ObjectId(job_id)})
    # check if sensor is part of that fixed job
    if not update_job:
        return "Not found"

    if sensor not in update_job["sensors"]:
        return "Not included"

    # set key-value pair for sensor in 'states', if key doesn't exist it will be created
    result = await fixed_jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"states." + sensor: status}}
    )

    # change status depending on new states
    updated_job = await fixed_jobs_collection.find_one({"_id": ObjectId(job_id)})
    sensor_states = updated_job["states"]

    # if at least one state is failed -> failed
    # if all states are finished -> finished
    # otherwise if at least one state is running -> running
    failed = False
    finished = True
    running = False
    for key, value in sensor_states.items():
        if value.startswith("failed"):
            failed = True
        if not value.startswith("finished"):
            finished = False
        if value.startswith("running"):
            running = True
    print("failed: {}, finished: {}, running: {}".format(failed, finished, running))
    fix_job = updated_job["name"]
    if failed:
        await set_status(fix_job, "failed")
    elif finished:
        await set_status(fix_job, "finished")
    elif running:
        await set_status(fix_job, "running")
        await sensors_collection.update_many({},
                                             {"$pull": {"jobs": fix_job}})  # pull job from job lists once it's running
    # else it stays pending

    # returns a document with matchedCount, modifiedCount, upsertedId, acknowledged. See MongoDB docs for updateOne().
    return result


async def delete_fixed_job(name: str):
    # return and delete the document matching 'id'
    result = await fixed_jobs_collection.find_one_and_delete({"name": name})
    # remove the pointer to this fixed job from all job lists
    await sensors_collection.update_many({}, {"$pull": {"jobs": result["name"]}})
    # returns either the deleted document, or null if no document matched
    return result


async def return_fixed_jobs():
    fixed_jobs = []
    # returns a cursor to all documents in the collection
    fixed_jobs_cursor = fixed_jobs_collection.find().sort("start_time", pymongo.DESCENDING)
    # iterate the cursor and return all documents in a list, parameter length determines max length of the list
    for fixed_job in await fixed_jobs_cursor.to_list(length=None):
        fixed_jobs.append(fixed_jobs_helper(fixed_job))
    return fixed_jobs


async def return_pending_fixed_jobs_by_sensorname(sensor_name: str):
    sensor_name = str(sensor_name)
    if not uses_allowed_characters(sensor_name):
        return "invalid input"
    fixed_jobs = []
    # returns a cursor to all documents in the collection
    fixed_jobs_cursor = fixed_jobs_collection.find(
        {"sensors": sensor_name, "status": {"$in": ["pending"]}}).sort("start_time", pymongo.ASCENDING)
    # iterate the cursor and return all documents in a list, parameter length determines max length of the list
    for fixed_job in await fixed_jobs_cursor.to_list(length=None):
        fixed_jobs.append(fixed_jobs_helper(fixed_job))
    return fixed_jobs



async def return_fixed_job_by_job_id(job_id: str):
    job = await fixed_jobs_collection.find_one({"_id": ObjectId(job_id)})
    if job:
        return fixed_jobs_helper(job)


# -----------------------------------------
# ----------- TOKEN METHODS ---------------
# -----------------------------------------

# acces-token blacklist
async def add_token_to_blacklist(jti: str, subject: str, expire_timestamp: int):
    success = False
    time_added = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    exp_time_str = datetime.utcfromtimestamp(expire_timestamp).strftime("%Y-%m-%d %H:%M:%S")

    print(f"__add_token_to_blacklist: jti={jti}, exp={exp_time_str}")

    # add tokens with jti unique identifier, subject (sensor/user-name), expire_timestamp and time_added as '%Y-%m-%d %H:%M:%S'-string
    success = await token_blacklist.insert_one(
        {"jti": jti, "sub": subject, "expire": exp_time_str, "time_added": time_added})

    # every time a token is added to the blacklist, delete expired tokens
    await __delete_expired_tokens_list(token_blacklist)
    return success


async def remove_token_from_blacklist(jti: str):
    return await __remove_token_from_list(jti, token_blacklist)


async def check_token_in_blacklist(jti: str):
    return await __check_token_in_list(jti, token_blacklist)


async def delete_expired_tokens_blacklist():
    return await __delete_expired_tokens_list(token_blacklist)


async def remove_token_by_name_from_blacklist(sub: str):
    return await __remove_token_by_name_from_list(sub, token_blacklist)


# refresh-token whitelist
async def add_token_to_whitelist(jti: str, subject: str, expire_timestamp: int, sibling_jti: str = "None",
                                 sibling_exp: int = "None"):
    success = False
    time_added = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    exp_time_str = datetime.utcfromtimestamp(expire_timestamp).strftime("%Y-%m-%d %H:%M:%S")

    print(f"__add_token_to_whitelist: jti={jti}, exp={exp_time_str}")

    # add tokens with jti unique identifier, subject (sensor/user-name), expire_timestamp and time_added as '%Y-%m-%d %H:%M:%S'-string
    success = await token_whitelist.insert_one(
        {"jti": jti, "sub": subject, "expire": exp_time_str, "time_added": time_added, "sibling_jti": sibling_jti,
         "sibling_exp": sibling_exp})

    # every time a token is added to the blacklist, delete expired tokens
    await __delete_expired_tokens_list(token_whitelist)
    return success


async def remove_token_from_whitelist(jti: str):
    return await __remove_token_from_list(jti, token_whitelist)


async def check_token_in_whitelist(jti: str):
    return await __check_token_in_list(jti, token_whitelist)


async def delete_expired_tokens_whitelist():
    return await __delete_expired_tokens_list(token_whitelist)


async def remove_token_by_name_from_whitelist(sub: str):
    return await __remove_token_by_name_from_list(sub, token_whitelist)


async def get_refresh_token(sub: str) -> dict:
    ref_token = await token_whitelist.find_one({"sub": sub})
    if ref_token:
        return refresh_token_helper(ref_token)


# internal-token methods
async def __remove_token_from_list(jti: str, db_list: AsyncIOMotorCollection):
    success = False
    success = await db_list.delete_one({"jti": jti})
    if db_list == token_blacklist:
        print(f"__remove_token_from_blacklist: jti={jti}")
    elif db_list == token_whitelist:
        print(f"__remove_token_from_whitelist: jti={jti}")
    return success


async def __check_token_in_list(jti: str, db_list: AsyncIOMotorCollection):
    revoked_token = await db_list.find_one({"jti": jti})
    return revoked_token


async def __delete_expired_tokens_list(db_list: AsyncIOMotorCollection):
    # TODO: toptimize the time-handling
    now = datetime.now(timezone.utc)
    time_now = now.strftime("%Y-%m-%d %H:%M:%S")

    async for token in db_list.find():
        # print(token)
        expire = token["expire"]
        time1 = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S")
        time2 = datetime.strptime(time_now, "%Y-%m-%d %H:%M:%S")
        # print(int(diff_mins))
        if time2 > time1:
            await db_list.delete_one({"jti": token["jti"]})
            if db_list == token_blacklist:
                print(f"__delete_expired_tokens_blacklist: jti={token['jti']}, exp={time1} (now={time2})")
            elif db_list == token_whitelist:
                print(f"__delete_expired_tokens_whitelist: jti={token['jti']}, exp={time1} (now={time2})")
    return


async def __remove_token_by_name_from_list(sub: str, db_list: AsyncIOMotorCollection):
    if db_list == token_blacklist:
        list_str = "blacklist"
    elif db_list == token_whitelist:
        list_str = "whitelist"
    answer = await db_list.delete_many({"sub": sub})
    success = answer.acknowledged
    count = answer.deleted_count
    if success:
        print(f"__remove_token_by_name_from_{list_str}: removed {count} tokens for sub={sub}")
    else:
        print(f"__remove_token_by_name_from_{list_str}: removed no tokens for sub={sub}")
    return success


# -----------------------------------------
# ----------- USER METHODS ----------------
# -----------------------------------------


# add new user
async def add_user(email: str, username: str, password: str, role: str):
    # check inputs
    if not uses_allowed_characters(email):
        return False, "Invalid email."
    if not uses_allowed_characters(username):
        return False, "Invalid username."
    if not is_allowed_user_role(role):
        return False, "Invalid role."
    already_exists = await user_collection.find_one({"username": username})
    if already_exists:
        return False, "Username already used"
    # create user
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)
    insert_dict = user_default_dict.copy()
    insert_dict["email"] = email
    insert_dict["username"] = username
    insert_dict["hashed_password"] = hash
    insert_dict["role"] = role
    insert_dict["creation_date"] = datetime.now(timezone.utc).timestamp()
    success = await user_collection.insert_one(insert_dict)

    return success, ""


# validate user credentials
async def validate_user_pw(username: str, password: bytes):
    # check inputs
    if not uses_allowed_characters(username):
        return False
    # check validity of inputs
    valid_user = False
    current_user = await user_collection.find_one({"username": username})
    if current_user:
        valid_user = (bcrypt.checkpw(password, current_user["hashed_password"]))

    return valid_user


# get user data
async def return_user(username: str):
    current_user = await user_collection.find_one({"username": username})
    if current_user:
        user_email = current_user["email"]
        user_role = current_user["role"]

        return {"email": user_email,
                "username": username,
                "role": user_role}
    else:
        return None


# get user role
async def return_user_role(username: str):
    current_user = await user_collection.find_one({"username": username})
    user_role = current_user["role"]

    return user_role


# delete user
async def delete_user_db(email: str, username: str):
    # use the email for double-check (avoid input-mistakes and delete wrong user)
    user = await return_user(username)
    if not user:
        return False
    if user["username"] != username or user["email"] != email:
        return False
    return await user_collection.delete_one({"username": username})


# Retrieve list of all users
async def get_all_users_list():
    all_users = []
    all_users_cursor = user_collection.find()
    for user in await all_users_cursor.to_list(length=None):
        all_users.append(user_helper(user))
    return all_users


# Retrieve job list with matching ID
async def get_db_user(_id: str) -> dict:
    user = await user_collection.find_one({"_id": ObjectId(_id)})
    if user:
        return user_helper(user)


async def change_db_user_pw(_id: str, new_password: str) -> bool:
    bytes = new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    new_hash = bcrypt.hashpw(bytes, salt)
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"hashed_password": new_hash}})
    if updated_user:
        return True
    return False


async def change_db_user_email(_id: str, new_email: str) -> bool:
    if not uses_allowed_characters(new_email):
        return False
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"email": new_email}})
    if updated_user:
        return True
    return False

async def change_db_user_role(_id: str, new_role: str) -> bool:
    if not is_allowed_user_role(new_role):
        return False
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"role": new_role}})
    if updated_user:
        return True
    return False

async def change_db_user_rsa_key(_id: str, new_key: str) -> bool:
    if not uses_allowed_characters(new_key):
        return False
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"public_rsa_key": new_key}})
    if updated_user:
        return True
    return False

async def change_db_user_modify_online(username: str) -> bool:
    time_now = datetime.now(timezone.utc).timestamp()
    print(f"DEBUG: change_db_user_modify_online: time_now={time_now}")
    user = await user_collection.find_one({"username": username})
    if not user:
        return False
    user_id = user["_id"]
    online_history = user["online_status"]
    last_login, last_online = online_history[0]
    if abs(time_now - last_online) < 2*60*60:  # check if the user continued to work (and refreshed)
        online_history[0] = (last_login, time_now)
    else:  # else the user did log in new
        online_history.insert(0, (time_now, time_now))
        if len(online_history) > 100:
            online_history.pop()
    updated_user = await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"online_status": online_history}})
    if updated_user:
        return True
    return False

async def change_db_user_add_owned_sensor(_id: str, sensor_name: str) -> bool:
    user = await user_collection.find_one({"_id": ObjectId(_id)})
    if not user:
        return False
    sensor = await sensors_collection.find_one({"sensor_name": sensor_name})
    if not sensor:
        return False
    new_sensor_id = sensor["_id"]
    new_sensor_pair = (sensor_name, new_sensor_id)
    owned_sensors = user["owned_sensors"]
    owned_sensors.append(new_sensor_pair)
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"owned_sensors": owned_sensors}})
    if updated_user:
        return True
    return False

async def change_db_user_remove_owned_sensor(_id: str, sensor_name: str) -> bool:
    user = await user_collection.find_one({"_id": ObjectId(_id)})
    if not user:
        return False
    owned_sensors = user["owned_sensors"]
    for i in range(len(owned_sensors), 0, -1):
        current_name, current_id = owned_sensors[i]
        if current_name == sensor_name:
            owned_sensors.pop(i)
    updated_user = await user_collection.update_one({"_id": ObjectId(_id)}, {"$set": {"owned_sensors": owned_sensors}})
    if updated_user:
        return True
    return False




