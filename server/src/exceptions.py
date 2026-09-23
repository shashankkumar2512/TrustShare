from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class AppException(HTTPException):
    pass

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})
