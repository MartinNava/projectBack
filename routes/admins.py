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

from models.admin import adminUpdate, registerAdmin

from middlewares.auth import validateRequest

router = APIRouter(prefix="/api/admin")

dbName = os.environ.get("MDBC_Name")

client = MongoClient(getMongoURL())
db = client[dbName]
tbName = os.environ.get("MDB_AName")


@router.get("/")
async def getAdmins(request: Request, search: Optional[str] = "", limit: Optional[str] = "10", skip: Optional[str] = "0") -> JSONResponse:
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    query = {}
    if search != "":
        query = {"$or": [{"name": {"$regex": search, "$options": "i"}}, {"last_name": {"$regex": search, "$options": "i"}}, {
            "email": {"$regex": search, "$options": "i"}}, {"phone": {"$regex": search, "$options": "i"}}]}
    admins = list(db[tbName].find(
        query, {"password": 0}, limit=int(limit), skip=int(skip)))
    countInDB = db[tbName].count_documents(query)

    if admins is None:
        return JSONResponse(status_code=500, content={"error": "Error detected"})

    return JSONResponse(status_code=200, content={"admins": admins, "totalInDB": countInDB})


@router.patch("/{id}")
def updateAdmin(id: str, adminInfo: adminUpdate, request: Request):
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    timeStamp = datetime.today().strftime("%Y-%m-%d")
    updateAdm = {
        "name": adminInfo.name,
        "last_name": adminInfo.last_name,
        "phone": adminInfo.phone,
        "lastUpdate": timeStamp,
        "lastUpdateBy": f"{reqStatus['name']} {reqStatus['last_name']}"
    }

    admUpdate = db[tbName].find_one_and_update(
        {"_id": id}, {"$set": updateAdm}, return_document=ReturnDocument.AFTER)

    if admUpdate is None:
        return JSONResponse(status_code=404, content={"error": "Admin not founded"})

    return JSONResponse(status_code=200, content={"message": "Admin has been updated successfully"})


@router.delete("/{id}")
def deleteAdmin(id: str, request: Request):
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    admDelete = db[tbName].delete_one({"_id": id})

    if admDelete is None:
        return JSONResponse(status_code=404, content={"error": "Admin not founded"})

    return JSONResponse(status_code=200, content={"message": "Admin has been deleted successfully"})


@router.post("/register")
def adminRegistration(admin: registerAdmin, request: Request):
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    adminInDB = db[tbName].find_one({"email": admin.email})
    if(adminInDB is not None):
        return JSONResponse(status_code=400, content={"error": "There's an existing account with that e-mail"})
    else:
        timeStamp = datetime.today().strftime("%Y-%m-%d")
        admin.password = bcrypt.hashpw(
            admin.password.encode(), bcrypt.gensalt())
        admSchema = {
            "_id": random_object_id.generate(),
            "name": admin.name,
            "last_name": admin.last_name,
            "email": admin.email,
            "phone": admin.phone,
            "password": admin.password,
            "type": "admin",
            "suspended": admin.suspended,
            "joinedAt": timeStamp,
            "lastUpdate": timeStamp,
            "lastUpdateBy": "New Account"
        }

        admId = db[tbName].insert_one(admSchema)

        return JSONResponse(status_code=200, content={"message": "Admin has been created successfully", "id": admId.inserted_id})
