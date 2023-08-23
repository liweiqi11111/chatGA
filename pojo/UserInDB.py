from pydantic import BaseModel

class UserInDB(BaseModel):
    user_id: int
    username: str
    hashed_password: str