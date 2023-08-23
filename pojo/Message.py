from pydantic import BaseModel
from datetime import datetime
from enum import Enum
# Role是一个枚举类，要么是user，要么是system
class Role(str, Enum):
    user = "user"
    system = "system"

class Message(BaseModel):
    msg_id: int
    conv_id: int
    role: Role
    content: str
    content_type: str
    create_time: datetime

