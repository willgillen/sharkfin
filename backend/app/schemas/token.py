from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data encoded in JWT token."""
    email: Optional[str] = None
