import logging

from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.route.user_routers import router as user_router
from app.exceptions import UserNotFoundError, EmailNotAllowedNameExistsError
from app.logging import init_logging, create_logger

app = FastAPI()
init_logging()
logger = create_logger('global_handler')

@app.exception_handler(EmailNotAllowedNameExistsError)
async def email_not_allowed_handler(request: Request, exc: EmailNotAllowedNameExistsError):
    logger.exception("Email Not Allowed exception occurred")
    # logger.error("Email Not Allowed exception occurred", exc_info=exc)
    return JSONResponse(
        status_code=409,
        content={"error": "Email Not Allowed", "message": str(exc)}
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    logger.exception("User Not Found exception occurred")
    # logger.error("User Not Found exception occurred", exc)
    return JSONResponse(
        status_code=404,
        content={"error": "User Not Found", "message": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.exception("Bad Request exception occurred")
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "message": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.exception("HTTP exception occurred")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Exception", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong"}
    )

logger.info("앱 시작")

app.include_router(user_router)


@app.get("/hello")
def hello():
    logger.info("앱 시작")
    return {"message": "Hello FastAPI!"}
