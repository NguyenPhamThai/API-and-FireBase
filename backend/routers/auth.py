from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from ..schemas.auth_schema import UserInfo
from ..services import auth_service
from .. import database

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """
    Get current user information
    Requires Bearer token (Firebase ID token) in Authorization header
    Frontend has already authenticated with Firebase
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    id_token = authorization.split(" ")[1]
    
    # Verify Firebase ID token (using Admin SDK)
    user_data = auth_service.verify_id_token(id_token)
    user_id = user_data["uid"]
    
    # Ensure user exists in local database
    if not database.user_exists(user_id):
        database.create_user(user_id, user_data["email"])
    
    # Get user from database
    user = database.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return UserInfo(
        user_id=user["id"],
        email=user["email"],
        created_at=user.get("created_at")
    )

