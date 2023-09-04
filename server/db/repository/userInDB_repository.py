from server.db.models.userInDB_model import UserInDBModel
from server.db.session import with_session

from passlib.context import CryptContext   

# 配置数据库连接
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@with_session
def get_user(session, username: str):
    user = session.query(UserInDBModel).filter_by(username=username).first()
    if not user:
        return None
    return user

@with_session
def authenticate_user(session, username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user.password):
        return False
    return True

@with_session
def create_user(session, username: str, password: str):
    user = get_user(username)
    if user:
        return False
    hashed_password = pwd_context.hash(password)
    user = UserInDBModel(username=username, password=hashed_password)
    session.add(user)
    return True


