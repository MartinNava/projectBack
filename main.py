from urllib.request import Request
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.requests import Request
import uvicorn
from dotenv import load_dotenv

from routes.admins import router as AdminRouter
from routes.log import router as LogRouter
from routes.users import router as UserRouter
from routes.modelDatabase import router as ModelDatabaseRouter

from middlewares.auth import validateRequest

load_dotenv()

app = FastAPI()


@app.get("/api")
def apiCall():
    return JSONResponse(status_code=200, content={"message": "Api correcta"})


@app.get("/api/verify")
def verifyToken(request: Request):
    reqStatus = validateRequest(request, ["admin"])
    if reqStatus["status"] != 200:
        return JSONResponse(status_code=reqStatus["status"], content={"error": reqStatus["error"], "verify": False})

    return JSONResponse(status_code=200, content={"message": "Verified", "verify": True})


app.include_router(LogRouter)
app.include_router(AdminRouter)
app.include_router(UserRouter)
app.include_router(ModelDatabaseRouter)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
