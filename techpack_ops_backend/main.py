from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth import auth_backend, fastapi_users, current_active_user, current_admin_user
from schemas.user import UserRead, UserCreate, UserUpdate
from models.user import User

app = FastAPI(title="Techpack Ops API")

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000", "http://localhost:5179"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {"status": "healthy"}
