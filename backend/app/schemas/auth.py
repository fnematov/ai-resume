from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    org_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class RegisterOrganization(BaseModel):
    """Public self-service signup: creates an org (pending) + its first org_admin."""

    organization_name: str = Field(min_length=2, max_length=160)
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(Token):
    user: UserOut


class UpdateMe(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
