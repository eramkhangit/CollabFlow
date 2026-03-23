from passlib.context import CryptContext 
from app.config.config import get_settings

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
    Password verify karo - automatically handles Argon2/bcrypt both
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print("Password verification failed")
        return False

def verify_and_update_password(plain_password: str, hashed_password: str):
    """
    Password verify karo aur agar old algorithm (bcrypt) hai to upgrade kar do Argon2 mein
    """
    try:
        is_valid, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return is_valid, new_hash
    except Exception as e:
       
        print("Password verification/update failed")
        return False, None