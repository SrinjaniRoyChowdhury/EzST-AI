from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from app.db.supabase_client import get_supabase_admin

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = credentials.credentials
    supabase = get_supabase_admin()
    
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # user.user_metadata is a dict from Supabase
        metadata = user.user_metadata if isinstance(user.user_metadata, dict) else {}
            
        return {
            "sub": user.id,
            "email": user.email,
            "role": metadata.get("role", "seller"),
            "user_metadata": metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

CurrentUser = Annotated[dict, Depends(get_current_user)]