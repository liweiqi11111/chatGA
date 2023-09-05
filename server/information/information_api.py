from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Union
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from server.utils import BaseResponse, ListResponse
from server.information.service.information_service import InformationService
from server.information.User import User

# 创建用于JWT令牌签名的随机密钥：openssl rand -hex 32
# JWT令牌签名算法：HS256，令牌过期时间：60分钟
SECRET_KEY = "8bc1d6b8eb35aa64ed017d0c049bc34a3d035263b8d03fb4bb55693ad9c81549"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# 定义令牌端点相应的Pydantic模型
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


# 配置OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

infoService = InformationService()

# 创建生成新的访问令牌的工具函数
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


# get_current_user()函数用于验证JWT令牌并返回当前用户
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = infoService.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


## 创建并返回真正的JWT访问令牌
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    s = infoService.authenticate_user(
        username=form_data.username, password=form_data.password)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 注册接口
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    # 查询用户是否已存在
    if infoService.get_user(username=form_data.username):
        raise HTTPException(status_code=400, detail="用户已存在")
    # 创建用户
    status = infoService.create_user(username=form_data.username, password=form_data.password)
    if not status:
        raise HTTPException(status_code=400, detail="创建用户失败")
    return BaseResponse(code=200, msg="创建用户成功")

async def get_conversations(
    page: int = 1, 
    page_size: int = 10,
    current_user: User = Depends(get_current_user)
):    
    conversations = infoService.get_conversations(
        user_id=current_user.user_id, page=page, page_size=page_size)
    return ListResponse(data=conversations) 

async def get_messages(conv_id: int,  current_user: User = Depends(get_current_user)):
    messages = infoService.get_messages(conv_id=conv_id)
    return ListResponse(data=messages)

# 创建会话
async def create_conversation(current_user: User = Depends(get_current_user)):
    infoService.create_conversation(user_id=current_user.user_id)
    return BaseResponse(code=200, msg="创建会话成功, 默认标题为'新的会话'")


# 更新会话
async def update_conversation(
    conv_id: int, title: str,  current_user: User = Depends(get_current_user)
):
    infoService.update_conversation_title(conv_id=conv_id, title=title)
    return BaseResponse(code=200, msg="更新成功")


# 删除会话
async def delete_conversation(
    conv_id: int,  current_user: User = Depends(get_current_user)):
    status = infoService.delete_conversation(conv_id=conv_id)
    if not status:
        raise HTTPException(status_code=400, detail="删除失败, 会话不存在")
    return BaseResponse(code=200, msg="会话及其消息删除成功")

# 创建消息
async def create_message(
    conv_id: int,
    role: str,
    content: str,
    content_type: str,
    current_user: User = Depends(get_current_user)
):
    infoService.create_message(
        conv_id=conv_id, role=role, content=content, content_type=content_type
    )
    return BaseResponse(code=200, msg="创建成功")
