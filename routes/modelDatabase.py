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
import json

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from config.mongo import getMongoURL

from models.modelDatabase import registerElement, evaluateElement

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


@router.post("/model")
def trainModel():
    query = {}
    data = list(db[tbMName].find(query, {"_id": 0}))
    countInDB = db[tbMName].count_documents(query)

    dataFrame = pd.DataFrame(data)
    dataFrame["Outcome"] = dataFrame["Outcome"].replace([0, 1], ["Sano", "Enfermo"])
    
    X = dataFrame.drop("Outcome", axis = 1)
    Y = dataFrame["Outcome"]
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = 0.2)
    dt = DecisionTreeClassifier()
    dt.fit(X_train, Y_train)
    dump(dt, "modelo.joblib")

    return JSONResponse(status_code=200, content={"message": "Petición Correcta", "precisionDelModelo": str(dt.score(X_test, Y_test))})


@router.post("/model-prediction")
def prediction(data: evaluateElement):
    dt = load("modelo.joblib")

    datosEntrada = np.array([
        data.Pregnancies,
        data.Glucose,
        data.BloodPresure,
        data.SkinThickness,
        data.Insulin,
        data.BMI,
        data.DiabetesPedigreeFunction,
        data.Age
    ])

    resultado = dt.predict(datosEntrada.reshape(1, -1))
    return JSONResponse(status_code=200, content={"message": "Se ha realizado la petición", "Resultado": str(resultado[0])})