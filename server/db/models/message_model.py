from sqlalchemy import Column, Integer, String, DateTime, func
from server.db.base import Base

class MessageModel(Base):
    """
    消息模型
    """
    __tablename__ = 't_message'
    msg_id = Column(Integer, primary_key=True, autoincrement=True, comment='消息ID')
    conv_id = Column(Integer, comment='会话ID')
    role = Column(String, comment='角色user/system')
    content = Column(String, comment='消息内容')
    content_type = Column(String, comment='消息类型')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"<Message(id='{self.msg_id}', con_id='{self.conv_id}', role='{self.role}', content='{self.content}', content_type='{self.content_type}', create_time='{self.create_time}')>"