from pydantic import BaseModel
class Userinfo(BaseModel):
    user_input:str
class ProjectRequest(BaseModel):
    name:str
    remark:str|None
    
class ProjectMemberRequest(BaseModel):
    user_id: int
    project_id: int