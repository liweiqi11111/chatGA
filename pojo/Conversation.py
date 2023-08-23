from pydantic import BaseModel
from datetime import datetime

class Conversation(BaseModel):
    conv_id: int
    user_id: int
    # 设置默认值为：“新的对话”
    title: str = "新的对话"
    create_time: datetime
    update_time: datetime