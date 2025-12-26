from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# Request schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = Field(None, alias="isAdmin")


# Response schemas
class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    is_admin: bool = Field(alias="isAdmin")


class UserListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    is_admin: bool = Field(alias="isAdmin")
    created_at: datetime = Field(alias="createdAt")
