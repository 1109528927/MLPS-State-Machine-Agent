from pydantic import BaseModel,Field

class UserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    employee_no: str = Field(min_length=1, max_length=32)

class loginRequest(BaseModel):
    username: str
    password: str
  
