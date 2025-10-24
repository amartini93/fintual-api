from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    created_at: str
    updated_at: str
    balance: float = Field(0.0, description="Total user account balance in USD.")

    class Config:
        from_attributes = True
