from sqlalchemy import Column, Integer, String, DateTime, func

from server.db.base import Base

class ConversationModel(Base):
    """
    会话模型
    """
    __tablename__ = 't_conversation'
    conv_id = Column(Integer, primary_key=True, autoincrement=True, comment='会话ID')
    user_id = Column(Integer, comment='用户ID')
    title = Column(String, comment='会话名称')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<Conversation(id='{self.conv_id}', title='{self.title}', create_time='{self.create_time}', update_time='{self.update_time}')>"