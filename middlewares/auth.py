from os import getcwd
from typing import Dict
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import requests
from starlette.requests import Request

import random
import jwt

load_dotenv()

expirationDate = datetime.now()+timedelta(days=2)


def signJWT(id: int, email: str, name: str, last_name: str, type: str) -> Dict[str, str]:
    payload = {
        "rd": random.randint(0, 100000000),
        "id": id,
        "name": name,
        "last_name": last_name,
        "email": email,
        "type": type,
        "exp": expirationDate
    }

    f = open(f"{getcwd()}/keys/private.key", "r", encoding="utf8")

    token = jwt.encode(payload, f.read(), algorithm="RS256")
    f.close()
    


def auth(token: str, acceptedRoles) -> Dict[str, str]:
    try:
        f = open(f"{getcwd()}/keys/public.pub", "r", encoding="utf8")
        decoded = jwt.decode(token, f.read(), algorithms=["RS256"])
        f.close()
        if decoded["type"] in acceptedRoles:
            return{"status": 200, **decoded}
        else:
            return{"status": 401, "error": "Your credentials doesn't have the privileges to access this info"}
    except jwt.PyJWTError as error:
        print(error)
        return{"status": 400, "error": str(error)}


def validateRequest(request: Request, roles):
    print(request)
    if not "Authorization" in request.headers:
        return {"status": 400, "error": "Authorization not founded"}
    else:
        return auth(request.headers["Authorization"], roles)
