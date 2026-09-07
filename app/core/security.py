from passlib.context import CryptContext 
from app.config.config import get_settings
from datetime import datetime, timedelta, timezone
import uuid
from jose import JWTError, jwt
from typing import Dict, Any
from fastapi import HTTPException, status
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

settings = get_settings()

# logger = logging.getLogger(__name__)

# Password hashing context
# pwd_context = CryptContext(
#     schemes=["argon2", "bcrypt"],
#     deprecated="auto",
#     argon2__memory_cost=102400,
#     argon2__time_cost=3,
#     argon2__parallelism=4,
#     argon2__hash_len=32,
# )

# def hash_password(password: str) -> str:
#     """
#     Password hash using Argon2id
#     """
#     try:
#         return pwd_context.hash(password)
#     except Exception as e:
#         print((f"Password hashing failed"))
#         raise

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     try:
#         return pwd_context.verify(plain_password, hashed_password)
#     except Exception as e:
#         print(f"Password verification failed: {type(e).__name__}: {e}")
#         return False

ph = PasswordHasher(
    time_cost=3,
    memory_cost=102400,
    parallelism=4,
    hash_len=32,
)

def hash_password(password: str) -> str:
    try:
        return ph.hash(password)
    except Exception as e:
        print(f"Password hashing failed: {e}")
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except InvalidHash:
        print("Stored hash is not a valid argon2 hash")
        return False
    except Exception as e:
        print(f"Password verification failed: {type(e).__name__}: {e}")
        return False

# def create_access_token(data: dict) -> str:

#     payload = data.copy()

#     expire = datetime.now(timezone.utc) + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )

#     payload.update({
#         "exp": expire,
#         "type": "access"
#     })

#     return jwt.encode(
#         payload,
#         settings.SECRET_KEY,
#         algorithm=settings.ALGORITHM
#     )
def create_access_token(user_id: str, role: str, email: str | None = None) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
    }
    if email:
        payload["email"] = email

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["exp"] = expire

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id: str, jti: str) -> str:
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_and_update_password(plain_password: str, hashed_password: str):
    """
    Verify password; if hash params are outdated, return a new hash to save.
    """
    try:
        ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False, None
    except InvalidHash as e:
        print(f"Invalid hash format: {e}")
        return False, None

    # valid password — check if it needs rehashing (e.g. params changed)
    if ph.check_needs_rehash(hashed_password):
        new_hash = ph.hash(plain_password)
        return True, new_hash

    return True, None
    
def decode_token(token: str) -> Dict[str, Any]:
    
    if not token or not token.strip():
        raise ValueError("Token cannot be empty")
    
    #  Get Decoding Parameters
    secret_key = settings.SECRET_KEY
    algorithm = settings.ALGORITHM
    
    # Attempt Decoding
    try:
        payload = jwt.decode(
            token,                   
            secret_key,             
            algorithms=[algorithm]   
        )
        
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired. Please refresh token.")
        
    except jwt.InvalidSignatureError:
        raise ValueError("Invalid token signature. Token may be tampered.")
        
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
        
    except JWTError as e:
        raise ValueError(f"Token decode failed: {str(e)}")
    
    #  Validate Required Claims 
    if "sub" not in payload:
        raise ValueError("Token missing required 'sub' claim")
    
    
    if "exp" in payload:
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        current_datetime = datetime.now(timezone.utc)
        
        if current_datetime > exp_datetime:
            raise ValueError("Token has expired")

    return payload     

def decode_refresh_token(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )