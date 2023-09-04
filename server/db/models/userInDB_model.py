from sqlalchemy import Column, Integer, String, DateTime, func

from server.db.base import Base


class UserInDBModel(Base):
    """
    用户模型
    """
    __tablename__ = 't_user'
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = Column(String, comment='用户名')
    hashed_password = Column(String, comment='加密后密码')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"<User(id='{self.user_id}', username='{self.username}')>"
