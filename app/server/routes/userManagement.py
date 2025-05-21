# management functions for user accounts
from fastapi import APIRouter, Depends, Request, HTTPException, Security, status, Header, Response
from fastapi.responses import FileResponse
from fastapi_another_jwt_auth import AuthJWT
from app.server.models.userManagement import UserRegister, UserPwChange, ResponseModel, ErrorResponseModel
from app.server.routes.login import validate_access_token_rights, logout, revoke_tokens_by_sub, \
    verify_tokens_is_admin_or_target_sub
from datetime import timedelta, datetime
import os
import zipfile
from starlette.background import BackgroundTasks

from app.server.database import (
    add_user,
    delete_user_db,
    get_all_users_list,
    get_db_user,
    change_db_user_pw,
    change_db_user_email,
    change_db_user_role,
    change_db_user_rsa_key,
    change_db_user_add_owned_sensor,
    change_db_user_remove_owned_sensor,
)

router = APIRouter()

user_role_list = ["admin", "user"] #list of all possible user roles (used for dropdowns)

#return the above defined user-role-list
@router.get("/get_role_list", response_description="User role list retrieved")
async def get_user_role_list():
    global user_role_list
    return ResponseModel(user_role_list, "User role list retrieved successfully")



# register new user
@router.post('/register_user')
async def register_user(user: UserRegister, _Authorize: AuthJWT = Depends()):
    # requires permissions:admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    # currently registered "test users:"
    # 1. username: alice                 2. username: bob                3. username: dummy
    #   password: alice123                 password: bob123                password: dummy123
    #   email: alice@email.com             email: bob@email.com            email: dummy@email.com
    #   role: user                         role: admin                     role: sensor

    added_user, error_msg = await add_user(user.email, user.username, user.password, user.role)
    if not added_user:
        return ErrorResponseModel(500, "Error: " + error_msg)
    return ResponseModel("", "Registration Successful")


@router.delete('/delete_user')
async def delete_user(user: UserRegister, Authorize: AuthJWT = Depends()):
    # permissions: admin
    if not await validate_access_token_rights(Authorize=Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    user_deleted = await delete_user_db(user.email, user.username)
    if not user_deleted:
        return ErrorResponseModel(500, "Could not delete user.")
    # if the current user is deleted, log out
    if user.username == Authorize.get_raw_jwt()["sub"]:
        await logout(Authorize=Authorize)
    # else remove the users token from whitelist and add user to blacklist
    else:
        await revoke_tokens_by_sub(user.username)

    return ResponseModel("", "User successfully deleted.")


@router.get("/get_user_list")
async def get_user_list(_Authorize: AuthJWT = Depends()):
    # permissions: admin, user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    users_list = await get_all_users_list()
    if users_list:
        # only return the public available user information
        public_information = ["id", "username", "role", "online_status"]
        for user in users_list:
            for key in list(user.keys()):
                if key not in public_information:  # remove all information that are not public
                    user.pop(key, None)
                if key == "online_status":  # only keep the newest login
                    first_elem = user[key][0]
                    user[key] = [first_elem]

        return ResponseModel(users_list, "Users list successfully returned")
    return ResponseModel(users_list, "Empty list returned")


@router.get("/get_user_details/{_id}")
async def get_user_details(_id, _Authorize: AuthJWT = Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    user = await get_db_user(_id)
    if user:
        target_user = user["username"]
        if await verify_tokens_is_admin_or_target_sub(_Authorize, target_user):
            return ResponseModel(user, "User retrieved successfully")
    return ErrorResponseModel(404, "User doesn't exist.")


@router.put("/change_user_password/{_id}")
async def change_user_password(_id: str, pwChange: UserPwChange, _Authorize: AuthJWT=Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    user = await get_db_user(_id)
    if not user:
        return ErrorResponseModel(404, "User doesn't exist.")
    target_user = user["username"]
    if not await verify_tokens_is_admin_or_target_sub(_Authorize, target_user):
        return ErrorResponseModel(403, "Insufficient rights.")
    # correct user or admin
    if await change_db_user_pw(_id, pwChange.password):
        return ResponseModel("", "Password successfully updated.")
    return ErrorResponseModel(503, "Error during password update.")


@router.put("/change_user_email/{_id}")
async def change_user_email(_id: str, new_email: str, _Authorize: AuthJWT = Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["user", "admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    user = await get_db_user(_id)
    if not user:
        return ErrorResponseModel(404, "User doesn't exist.")
    target_user = user["username"]
    if not await verify_tokens_is_admin_or_target_sub(_Authorize, target_user):
        return ErrorResponseModel(403, "Insufficient rights.")
    # correct user or admin
    if await change_db_user_email(_id, new_email):
        return ResponseModel("", "Email successfully updated.")
    return ErrorResponseModel(503, "Error during email update.")

@router.put("/change_user_role/{_id}")
async def change_user_role(_id: str, new_role: str, _Authorize: AuthJWT = Depends()):
    # permissions: admin
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    if await change_db_user_role(_id, new_role):
        return ResponseModel("", "User role successfully updated.")
    return ErrorResponseModel(503, "Error during user role update.")

@router.put("/change_user_rsakey/{_id}")
async def change_user_rsakey(_id: str, new_key: str, _Authorize: AuthJWT = Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")

    user = await get_db_user(_id)
    if not user:
        return ErrorResponseModel(404, "User doesn't exist.")
    target_user = user["username"]
    if not await verify_tokens_is_admin_or_target_sub(_Authorize, target_user):
        return ErrorResponseModel(403, "Insufficient rights.")
    # correct user or admin
    if await change_db_user_rsa_key(_id, new_key):
        return ResponseModel("", "User rsa-key successfully updated.")
    return ErrorResponseModel(503, "Error during user rsa-key update.")

@router.put("/user_add_owned_sensor/{_id}")
async def user_add_owned_sensor(_id: str, sensor_name: str, _Authorize: AuthJWT = Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    if await change_db_user_add_owned_sensor(_id, sensor_name):
        return ResponseModel("", "Users owned sensors successfully updated.")
    return ErrorResponseModel(503, "Error during users owned sensors update.")

@router.put("/user_remove_owned_sensor/{_id}")
async def user_remove_owned_sensor(_id: str, sensor_name: str, _Authorize: AuthJWT = Depends()):
    # permissions: admin, correct user
    if not await validate_access_token_rights(Authorize=_Authorize, required_permissions=["admin"]):
        return ErrorResponseModel(401, "Unauthorized.")
    if await change_db_user_remove_owned_sensor(_id, sensor_name):
        return ResponseModel("", "Users owned sensors successfully updated.")
    return ErrorResponseModel(503, "Error during users owned sensors update.")
        




