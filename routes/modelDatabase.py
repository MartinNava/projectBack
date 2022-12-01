from datetime import datetime
from fastapi import APIRouter, File, UploadFile
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from fastapi.responses import JSONResponse
from starlette.requests import Request
import random_object_id
import os
from typing import Optional
import pandas as pd
import numpy as np
from joblib import load, dump

from config.mongo import getMongoURL

from models.modelDatabase import registerElement

router = APIRouter(prefix="/api/model-database")

dbName = os.environ.get("MDBC_Name")

client = MongoClient(getMongoURL())
db = client[dbName]
tbMName = os.environ.get("MDB_MName")


@router.get("/registro")
def getAllData(request: Request, search: Optional[str] = ""):
    query ={}
    if search != "":
        query = {"$or": [{"_id": {"$regex": search, "$options": "i"}}]}
    data = list(db[tbMName].find(query))
    countInDB = db[tbMName].count_documents(query)

    return JSONResponse(status_code=200, content={"dataToTrain": data, "totalInDB": countInDB})


@router.post("/registro")
def dataRegistration(data: registerElement):
    toAdd = {
        "_id": random_object_id.generate(),
        "Pregnancies": data.Pregnancies,
        "Glucose": data.Glucose,
        "BloodPresure": data.BloodPresure,
        "SkinThickness": data.SkinThickness,
        "Insulin": data.Insulin,
        "BMI": data.BMI,
        "DiabetesPedigreeFunction": data.DiabetesPedigreeFunction,
        "Age": data.Age,
        "Outcome": data.Outcome
    }

    dataId = db[tbMName].insert_one(toAdd)

    return JSONResponse(status_code=200, content={"message": "Data has been added successfully", "id": dataId.inserted_id})


@router.delete("/registro/{id}")
def dataDeletion(id: str, request: Request):
    dataDelete = db[tbMName].delete_one({"_id": id})
    if dataDelete is None:
        return JSONResponse(status_code=404, content={"error": "Data not founded"})

    return JSONResponse(status_code=200, content={"message": "Data has been deleted successfully"})


@router.post("/train-model")
def trainModel():
    query = {}
    data = list(db[tbMName].find(query))
    countInDB = db[tbMName].count_documents(query)

    dataFrame = pd.read_json(data)

    print(dataFrame)

    return JSONResponse(status_code=200, content={"message": "Petición Correcta", "countInDB": countInDB})