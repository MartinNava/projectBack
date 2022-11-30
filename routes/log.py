from datetime import datetime
from fastapi import APIRouter
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from fastapi.responses import JSONResponse
from starlette.requests import Request
import bcrypt
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.mongo import getMongoURL

from models.log import loginModel, passwordChange, passwordRestore

from middlewares.auth import signJWT, validateRequest

router = APIRouter(prefix="/api/log")

dbName = os.environ.get("MDBC_Name")

client = MongoClient(getMongoURL())
db = client[dbName]
tbAName = os.environ.get("MDB_AName")
tbUName = os.environ.get("MDB_UName")


@router.post("/login")
def login(login: loginModel):
    loginData = db[tbAName].find_one(
        {"email": login.email}) or db[tbUName].find_one({"email": login.email})
    if loginData is not None:
        if bcrypt.checkpw(login.password.encode(), loginData["password"]):

            token = signJWT(
                loginData["_id"], loginData["email"], loginData["name"], loginData["last_name"], loginData["type"])

            return JSONResponse(status_code=200, content={"message": "Logged in", "admin": token["token"]})
        else:
            return JSONResponse(status_code=400, content={"message": "You must enter the correct password"})
    else:
        return JSONResponse(status_code=404, content={"error": "There's not an existing account"})


@router.get("/profile")
def profile(usr: str, request: Request):
    reqStatus = validateRequest(request, ["admin", "user"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    profile = list(db[tbAName].find({"_id": usr}, {"password": 0})) or list(
        db[tbUName].find({"_id": usr}, {"password": 0}))

    if profile is None:
        return JSONResponse(status_code=500, content={"error": "Error detected"})

    if usr != reqStatus["id"] and reqStatus["type"] == "user":
        return JSONResponse(status_code=400, content={"message": "You can't access to other profiles"})

    return JSONResponse(status_code=200, content={"profile": profile})


@router.post("/reset-password")
def resetPassword(usr: str, passChange: passwordChange, request: Request):
    reqStatus = validateRequest(request, ["admin", "user"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    usrInDB = db[tbAName].find_one(
        {"_id": usr}) or db[tbUName].find_one({"_id": usr})
    if usrInDB is None:
        return JSONResponse(status_code=404, content={"error": "User not founded"})
    else:
        if bcrypt.checkpw(passChange.password.encode(), usrInDB["password"]):
            timeStamp = datetime.today().strftime("%Y-%m-%d")
            passChange.newPassword = bcrypt.hashpw(
                passChange.newPassword.encode(), bcrypt.gensalt())
            updateUsr = {
                "password": passChange.newPassword,
                "lastUpdate": timeStamp,
                "lastUpdateBy": f"{reqStatus['name']} {reqStatus['last_name']}"
            }

            if reqStatus["type"] == "admin":
                usrUpdate = db[tbAName].find_one_and_update(
                    {"_id": usr}, {"$set": updateUsr}, return_document=ReturnDocument.AFTER)
            elif reqStatus["type"] == "user":
                usrUpdate = db[tbUName].find_one_and_update(
                    {"_id": usr}, {"$set": updateUsr}, return_document=ReturnDocument.AFTER)

            if usrUpdate is None:
                return JSONResponse(status_code=404, content={"error": "User not founded"})

            return JSONResponse(status_code=200, content={"message": "User has been updated successfully"})
        else:
            return JSONResponse(status_code=400, content={"message": "You must enter the correct password"})


@router.post("/restore-email")
def restoreEmail(email: str):
    loginData = db[tbAName].find_one(
        {"email": email}) or db[tbUName].find_one({"email": email})
    if loginData is not None:
        token = signJWT(
            loginData["_id"], loginData["email"], loginData["name"], loginData["last_name"], loginData["type"])

        message = MIMEMultipart("alternative")
        message["Subject"] = "Recuperacion de contraseña"
        message["From"] = "base_api@support.mx"
        message["To"] = email
        urlRestore = f"{os.environ.get('BASE_URL')}?tk={token}"
        bodyText = f"""\
            <html>
                <body>
                    <p>Servicio de reestablecimiento de contraseña</p>
                    <p>Para reestablecer su contraseña, por favor siga siga este <a href={urlRestore}>link</a>
                    <p><b>Base API</b></p>
                </body>
            </html>
        """
        htmlFormat = MIMEText(bodyText, "html")
        message.attach(htmlFormat)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(os.environ.get("GMAIL_USER"),
                         os.environ.get("GMAIL_PWD"))
            server.sendmail(os.environ.get("GMAIL_USER"),
                            email, message.as_string())
        return JSONResponse(status_code=200, content={"message": "Restore e-mail has sent successfully"})
    else:
        return JSONResponse(status_code=404, content={"error": "There's not an existing account"})


@router.post("/restore-password")
def restorePassword(passChange: passwordRestore, request: Request):
    reqStatus = validateRequest(request, ["admin", "user"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"]})

    timeStamp = datetime.today().strftime("%Y-%m-%d")
    passChange.password = bcrypt.hashpw(
        passChange.password.encode(), bcrypt.gensalt())
    updateUsr = {
        "password": passChange.password,
        "lastUpdate": timeStamp,
        "lastUpdateBy": f"{reqStatus['name']} {reqStatus['last_name']}"
    }

    if reqStatus["type"] == "admin":
        usrUpdate = db[tbAName].find_one_and_update(
            {"_id": reqStatus["id"]}, {"$set": updateUsr}, return_document=ReturnDocument.AFTER)
    elif reqStatus["type"] == "user":
        usrUpdate = db[tbUName].find_one_and_update(
            {"_id": reqStatus["id"]}, {"$set": updateUsr}, return_document=ReturnDocument.AFTER)

    if usrUpdate is None:
        return JSONResponse(status_code=404, content={"error": "User not founded"})

    return JSONResponse(status_code=200, content={"message": "User has been updated successfully"})
