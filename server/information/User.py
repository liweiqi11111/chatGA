from pydantic import BaseModel

class User(BaseModel):
    """
    用户模型
    """
    user_id: int
    username: str