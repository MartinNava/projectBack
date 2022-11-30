from datetime import datetime
from fastapi import APIRouter
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from fastapi.responses import JSONResponse
from starlette.requests import Request
import bcrypt
import random_object_id
import os
from typing import Optional

from config.mongo import getMongoURL

from models.user import userUpdate, registerUser

from middlewares.auth import validateRequest

router = APIRouter(prefix="/api/user")

dbName = os.environ.get("MDBC_Name")

client = MongoClient(getMongoURL())
db = client[dbName]
tbName = os.environ.get("MDB_UName")


@router.get("/")
async def getUsers(request: Request, search: Optional[str] = "", limit: Optional[str] = "10", skip: Optional[str] = "0") -> JSONResponse:
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    query = {}
    if search != "":
        query = {"$or": [{"name": {"$regex": search, "$options": "i"}}, {"last_name": {"$regex": search, "$options": "i"}}, {
            "email": {"$regex": search, "$options": "i"}}, {"phone": {"$regex": search, "$options": "i"}}]}
    users = list(db[tbName].find(
        query, {"password": 0}, limit=int(limit), skip=int(skip)))
    countInDB = db[tbName].count_documents(query)

    if users is None:
        return JSONResponse(status_code=500, content={"error": "Error detected"})

    return JSONResponse(status_code=200, content={"users": users, "totalInDB": countInDB})


@router.patch("/{id}")
def updateUser(id: str, userInfo: userUpdate, request: Request):
    reqStatus = validateRequest(request, ["admin", "user"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    timeStamp = datetime.today().strftime("%Y-%m-%d")
    updateUsr = {
        "name": userInfo.name,
        "last_name": userInfo.last_name,
        "phone": userInfo.phone,
        "lastUpdate": timeStamp,
        "lastUpdateBy": f"{reqStatus['name']} {reqStatus['last_name']}"
    }

    usrUpdate = db[tbName].find_one_and_update(
        {"_id": id}, {"$set": updateUsr}, return_document=ReturnDocument.AFTER)

    if usrUpdate is None:
        return JSONResponse(status_code=404, content={"error": "User not founded"})

    return JSONResponse(status_code=200, content={"message": "User has been updated successfully"})


@router.delete("/{id}")
def deleteUser(id: str, request: Request):
    reqStatus = validateRequest(request, ["admin", "user"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})
    
    if id != reqStatus["id"] and reqStatus["type"] == "user":
        return JSONResponse(status_code=400, content={"message": "You can't delete other profiles"})

    usrDelete = db[tbName].delete_one({"_id": id})

    if usrDelete is None:
        return JSONResponse(status_code=404, content={"error": "User not founded"})

    return JSONResponse(status_code=200, content={"message": "User has been deleted successfully"})


@router.post("/register")
def userRegistration(user: registerUser):
    userInDB = db[tbName].find_one({"email": user.email})
    if(userInDB is not None):
        return JSONResponse(status_code=400, content={"error": "There's an existing account with that e-mail"})
    else:
        timeStamp = datetime.today().strftime("%Y-%m-%d")
        user.password = bcrypt.hashpw(
            user.password.encode(), bcrypt.gensalt())
        usrSchema = {
            "_id": random_object_id.generate(),
            "name": user.name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "password": user.password,
            "type": "user",
            "suspended": user.suspended,
            "joinedAt": timeStamp,
            "lastUpdate": timeStamp,
            "lastUpdateBy": "New Account"
        }

        usrId = db[tbName].insert_one(usrSchema)

        return JSONResponse(status_code=200, content={"message": "User has been created successfully", "id": usrId.inserted_id})
