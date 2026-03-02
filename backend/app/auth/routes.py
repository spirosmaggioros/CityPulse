from app.auth.auth import create_access_token, hash_password, verify_password
from app.db import users_collection
from app.models import UserCreate, UserLogin, UserOut
from app.utils import verify_api_key
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])  # type: ignore
async def register(body: UserCreate) -> UserOut:
    existing = await users_collection.find_one({"username": body.username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    doc = {
        "username": body.username,
        "password_hash": hash_password(body.password),
    }
    result = await users_collection.insert_one(doc)

    return UserOut(id=str(result.inserted_id), username=body.username)


@router.post("/login")  # type: ignore
async def login(body: UserLogin) -> dict:
    user = await users_collection.find_one({"username": body.username})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=str(user["_id"]))
    return {"access_token": token, "token_type": "bearer"}
