from passlib.context import CryptContext 
from app.config.config import get_settings
from datetime import datetime, timedelta, timezone
import uuid
from jose import JWTError, jwt
from typing import Dict, Any

settings = get_settings()

# logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],  # Argon2 primary,  "bcrypt": if  "bcrypt" used bcrypt fallback for old users if we don't use bcrypt then old user can't login
    deprecated="auto",               # Auto-detect deprecated schemes
    
    # Argon2 parameters (This is OWASP recommended)
    argon2__memory_cost=102400,      # 100 MB memory 
    argon2__time_cost=3,             # 3 iterations
    argon2__parallelism=4,           # 4 threads 
    argon2__hash_len=32,             # 256-bit output
    
    # stop load bcrypt
    bcrypt__rounds=None,             
)

def hash_password(password: str) -> str:
    """
    Password hash using Argon2id
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print((f"Password hashing failed"))
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Password verify - automatically handles Argon2/bcrypt both
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception :
        print("Password verification failed")
        return False

def create_access_token(user_id:str, role:str) -> str:
    """Create JWT token"""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",     
        "jti": str(uuid.uuid4()), 
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
        }
        
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def create_refresh_token(user_id: str,jti: str) -> str:
    """refresh token generate a new access token"""

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "type": "refresh",         
        "jti": jti, 
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
    }
    
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def verify_and_update_password(plain_password: str, hashed_password: str):
    """
    verify password, if password is in bcrypt then upgrade into Argon2
    """
    try:
        is_valid, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return is_valid, new_hash
    except Exception as e:
       
        print("Password verification/update failed")
        return False, None
    
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