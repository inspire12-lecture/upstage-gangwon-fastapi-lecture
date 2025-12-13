from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel

from app.deps import get_user_service

# create user
router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: str


@router.post("/", response_model=UserResponse)
async def create_user_api(
        user_create_request: UserCreateRequest,
        user_service=Depends(get_user_service)
):
    user = user_service.create_user(name=user_create_request.name, email=user_create_request.email)
    return UserResponse(
        id=user.get('id'),
        name=user.get('name'),
        email=user.get('email'),
        created_at=user.get('created_at')
    )


@router.get("/", response_model=UserResponse)
async def get_user_api(
        user_id: int,
        user_service=Depends(get_user_service)
):
    user = user_service.get_user(
        user_id=user_id
    )
    return UserResponse(
        id=user.get('id'),
        name=user.get('name'),
        email=user.get('email'),
        created_at=user.get('created_at')
    )



@router.post("/", response_model=UserResponse)
async def create_user_api(
        user_create_request: UserCreateRequest,
):
    user_service = UserService()
    user_service.create_user(
        name=user_create_request.name,
        email=user_create_request.email
    )
    return UserResponse(
        id=0,
        name=user_create_request.name,
        email=user_create_request.email,
        created_at=str(datetime.now())
    )
