# encoding:utf-8
import argparse
import json
import os
import shutil
from typing import List, Optional
import urllib
import asyncio
import nltk
import pydantic
import uvicorn
from fastapi import Body, FastAPI, File, Form, Query, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing_extensions import Annotated
from starlette.responses import RedirectResponse

from chains.local_doc_qa import LocalDocQA
from configs.model_config import (
    KB_ROOT_PATH,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    NLTK_DATA_PATH,
    VECTOR_SEARCH_TOP_K,
    LLM_HISTORY_LEN,
    OPEN_CROSS_DOMAIN,
)
import models.shared as shared
from models.loader.args import parser
from models.loader import LoaderCheckPoint


import os

os.environ["CURL_CA_BUNDLE"] = ""

nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

###############################  NEW #################################
###############################  NEW #################################
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Union
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import db
import pojo.Conversation as Conversation, pojo.Message as Message
import db.dao as db
from db.User import User

class BaseResponse(BaseModel):
    code: int = pydantic.Field(200, description="HTTP status code")
    msg: str = pydantic.Field("success", description="HTTP status message")

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
            }
        }


class ListDocsResponse(BaseResponse):
    data: List[str] = pydantic.Field(..., description="List of document names")

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
                "data": ["doc1.docx", "doc2.pdf", "doc3.txt"],
            }
        }


class ConversationResponse(BaseResponse):
    data: List[Conversation.Conversation] = pydantic.Field(..., description="分页查询会话列表，按照更新时间排序")
    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "获取成功",
                "data": [
                    {
                        "conv_id": 2,
                        "user_id": 9,
                        "title": "政务问答2",
                        "create_time": "2023-08-23T16:19:56",
                        "update_time": "2023-08-23T16:20:00",
                    },
                    {
                        "conv_id": 1,
                        "user_id": 9,
                        "title": "政务问答",
                        "create_time": "2023-08-22T17:29:14",
                        "update_time": "2023-08-22T17:29:18",
                    },
                ],
            }
        }


class MessageResponse(BaseResponse):
    data: List[Message.Message] = pydantic.Field(..., description="分页查询会话列表，按照更新时间排序")

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "获取成功",
                "data": [
                    {
                        "msg_id": 1,
                        "conv_id": 1,
                        "role": "user",
                        "content": "政务问答：请问劳动法的条例有哪些？",
                        "content_type": "text",
                        "create_time": "2023-08-22T17:31:32",
                    },
                    {
                        "msg_id": 2,
                        "conv_id": 1,
                        "role": "system",
                        "content": "劳动法是针对劳动者与用人单位之间的劳动关系，以及保障劳动者权益和维护劳动秩序的法律法规。不同国家和地区的劳动法条例可能会有所不同。以下是一些常见的劳动法方面的条例，但请注意这只是一些典型的条例，具体内容可能因地区而异：\r\n\r\n1. **就业和招聘**：\r\n   - 禁止性别歧视\r\n   - 年龄歧视规定\r\n   - 招聘过程中的平等对待\r\n\r\n2. **合同与工资**：\r\n   - 劳动合同的签订和解除\r\n   - 工资支付和调整\r\n   - 加班工资和休息日规定\r\n\r\n3. **工时与休假**：\r\n   - 工作时间和休息时间规定\r\n   - 年假和带薪休假\r\n   - 法定节假日和特殊假期\r\n\r\n4. **劳动条件和保护**：\r\n   - 安全和健康保护\r\n   - 福利待遇、社会保险和福利\r\n   - 离职、辞退和解雇程序\r\n\r\n5. **劳动争议解决**：\r\n   - 劳动争议调解和仲裁\r\n   - 法院诉讼程序\r\n\r\n6. **工会和劳动组织**：\r\n   - 工会的组织和权利\r\n   - 工会与用人单位的关系\r\n\r\n7. **特殊群体保障**：\r\n   - 女性和儿童劳工的保护\r\n   - 残疾人员的就业权益保护\r\n\r\n请注意，每个国家和地区的劳动法条例都会有所不同，特别是在不同的文化、法律和社会背景下。如果您想了解具体的劳动法条例，最好是查询您所在地区的相关官方法律法规或咨询法律专业人士。",
                        "content_type": "text",
                        "create_time": "2023-08-22T17:31:58",
                    },
                ],
            }
        }


class ChatMessage(BaseModel):
    question: str = pydantic.Field(..., description="Question text")
    response: str = pydantic.Field(..., description="Response text")
    history: List[List[str]] = pydantic.Field(..., description="History text")
    source_documents: List[str] = pydantic.Field(
        ..., description="List of source documents and their scores"
    )

    class Config:
        schema_extra = {
            "example": {
                "question": "工伤保险如何办理？",
                "response": "根据已知信息，可以总结如下：\n\n1. 参保单位为员工缴纳工伤保险费，以保障员工在发生工伤时能够获得相应的待遇。\n2. 不同地区的工伤保险缴费规定可能有所不同，需要向当地社保部门咨询以了解具体的缴费标准和规定。\n3. 工伤从业人员及其近亲属需要申请工伤认定，确认享受的待遇资格，并按时缴纳工伤保险费。\n4. 工伤保险待遇包括工伤医疗、康复、辅助器具配置费用、伤残待遇、工亡待遇、一次性工亡补助金等。\n5. 工伤保险待遇领取资格认证包括长期待遇领取人员认证和一次性待遇领取人员认证。\n6. 工伤保险基金支付的待遇项目包括工伤医疗待遇、康复待遇、辅助器具配置费用、一次性工亡补助金、丧葬补助金等。",
                "history": [
                    [
                        "工伤保险是什么？",
                        "工伤保险是指用人单位按照国家规定，为本单位的职工和用人单位的其他人员，缴纳工伤保险费，由保险机构按照国家规定的标准，给予工伤保险待遇的社会保险制度。",
                    ]
                ],
                "source_documents": [
                    "出处 [1] 广州市单位从业的特定人员参加工伤保险办事指引.docx：\n\n\t( 一)  从业单位  (组织)  按“自愿参保”原则，  为未建 立劳动关系的特定从业人员单项参加工伤保险 、缴纳工伤保 险费。",
                    "出处 [2] ...",
                    "出处 [3] ...",
                ],
            }
        }


# 创建用于JWT令牌签名的随机密钥：openssl rand -hex 32
# JWT令牌签名算法：HS256，令牌过期时间：30分钟
SECRET_KEY = "8bc1d6b8eb35aa64ed017d0c049bc34a3d035263b8d03fb4bb55693ad9c81549"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    userInDB = db.get_user(username=token_data.username)
    if userInDB is None:
        raise credentials_exception
    return User(user_id=userInDB.user_id, username=userInDB.username)


app = FastAPI()


## 创建并返回真正的JWT访问令牌
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.authenticate_user(
        username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 注册接口
@app.post("/register/", response_model=BaseResponse)
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    # 查询用户是否已存在
    if db.get_user(username=form_data.username):
        raise HTTPException(status_code=400, detail="用户已存在")
    # 创建用户
    db.create_user(username=form_data.username, password=form_data.password)
    return BaseResponse(code=200, msg="注册成功")


##----- 需要进行登录拦截的接口 -----


# 分页获取用户的所有会话，并根据更新时间进行排序 conversations?offset=0&limit=28&order=updated
@app.get("/conversations/", response_model=ConversationResponse)
async def get_conversations(
    offset: int = 0,
    limit: int = 28,
    order: str = "updated",
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    conversations = db.get_conversations_by_user_id_with_orm(
        user_id=current_user.user_id, offset=offset, limit=limit, order=order
    )
    return ConversationResponse(code=200, msg="获取成功", data=conversations)
    # return {"code": 200, "msg": "获取成功", "data": conversations}


# 根据会话id获取会话信息，并根据创建时间进行排序 conversation/1
@app.get("/conversation/", response_model=MessageResponse)
async def get_messages(conv_id: int, current_user: User = Depends(get_current_user)):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    messages = db.get_messages_by_conv_id_with_orm(conv_id=conv_id)
    return MessageResponse(code=200, msg="获取成功", data=messages)
    # return {"code": 200, "msg": "获取成功", "data": messages}


# 创建会话
@app.post("/conversation/", response_model=BaseResponse)
async def create_conversation(current_user: User = Depends(get_current_user)):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    conv_id = db.create_conversation(user_id=current_user.user_id)
    return BaseResponse(code=200, msg="更新成功, 创建会话conv_id:{}, 默认标题为'新的会话'".format(conv_id))
    # return {"code": 200, "msg": "创建成功", "data": {"conv_id": conv_id}}


# 更新会话
@app.put("/conversation/", response_model=BaseResponse)
async def update_conversation(
    conv_id: int, title: str, current_user: User = Depends(get_current_user)
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    db.update_conversation(conv_id=conv_id, title=title)
    return BaseResponse(code=200, msg="更新成功")


# 删除会话
@app.delete("/conversation/", response_model=BaseResponse)
async def delete_conversation(
    conv_id: int, current_user: User = Depends(get_current_user)
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    db.delete_conversation(conv_id=conv_id)
    return BaseResponse(code=200, msg="删除成功")
    # return {"code": 200, "msg": "删除成功"}


# 创建消息
@app.post("/message/", response_model=BaseResponse)
async def create_message(
    conv_id: int,
    role: str,
    content: str,
    content_type: str,
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    db.create_message(
        conv_id=conv_id, role=role, content=content, content_type=content_type
    )
    return BaseResponse(code=200, msg="创建成功")


###############################  NEW #################################
###############################  NEW #################################




def get_kb_path(local_doc_id: str):
    return os.path.join(KB_ROOT_PATH, local_doc_id)


def get_doc_path(local_doc_id: str):
    return os.path.join(get_kb_path(local_doc_id), "content")


def get_vs_path(local_doc_id: str):
    return os.path.join(get_kb_path(local_doc_id), "vector_store")


def get_file_path(local_doc_id: str, doc_name: str):
    return os.path.join(get_doc_path(local_doc_id), doc_name)


def validate_kb_name(knowledge_base_id: str) -> bool:
    # 检查是否包含预期外的字符或路径攻击关键字
    if "../" in knowledge_base_id:
        return False
    return True


async def upload_file(
    file: UploadFile = File(description="A single binary file"),
    knowledge_base_id: str = Form(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return BaseResponse(code=403, msg="Don't attack me", data=[])

    saved_path = get_doc_path(knowledge_base_id)
    if not os.path.exists(saved_path):
        os.makedirs(saved_path)

    file_content = await file.read()  # 读取上传文件的内容

    file_path = os.path.join(saved_path, file.filename)
    if os.path.exists(file_path) and os.path.getsize(file_path) == len(file_content):
        file_status = f"文件 {file.filename} 已存在。"
        return BaseResponse(code=200, msg=file_status)

    with open(file_path, "wb") as f:
        f.write(file_content)

    vs_path = get_vs_path(knowledge_base_id)
    vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(
        [file_path], vs_path
    )
    if len(loaded_files) > 0:
        file_status = f"文件 {file.filename} 已上传至新的知识库，并已加载知识库，请开始提问。"
        return BaseResponse(code=200, msg=file_status)
    else:
        file_status = "文件上传失败，请重新上传"
        return BaseResponse(code=500, msg=file_status)


async def upload_files(
    files: Annotated[
        List[UploadFile], File(description="Multiple files as UploadFile")
    ],
    knowledge_base_id: str = Form(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return BaseResponse(code=403, msg="Don't attack me", data=[])

    saved_path = get_doc_path(knowledge_base_id)
    if not os.path.exists(saved_path):
        os.makedirs(saved_path)
    filelist = []
    for file in files:
        file_content = ""
        file_path = os.path.join(saved_path, file.filename)
        file_content = await file.read()
        if os.path.exists(file_path) and os.path.getsize(file_path) == len(
            file_content
        ):
            continue
        with open(file_path, "wb") as f:
            f.write(file_content)
        filelist.append(file_path)
    if filelist:
        vs_path = get_vs_path(knowledge_base_id)
        vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(
            filelist, vs_path
        )
        if len(loaded_files):
            file_status = f"documents {', '.join([os.path.split(i)[-1] for i in loaded_files])} upload success"
            return BaseResponse(code=200, msg=file_status)
    file_status = f"documents {', '.join([os.path.split(i)[-1] for i in loaded_files])} upload fail"
    return BaseResponse(code=500, msg=file_status)


async def list_kbs(current_user: User = Depends(get_current_user)):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    # Get List of Knowledge Base
    if not os.path.exists(KB_ROOT_PATH):
        all_doc_ids = []
    else:
        all_doc_ids = [
            folder
            for folder in os.listdir(KB_ROOT_PATH)
            if os.path.isdir(os.path.join(KB_ROOT_PATH, folder))
            and os.path.exists(
                os.path.join(KB_ROOT_PATH, folder, "vector_store", "index.faiss")
            )
        ]

    return ListDocsResponse(data=all_doc_ids)


async def list_docs(
    knowledge_base_id: str = Query(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return ListDocsResponse(code=403, msg="Don't attack me", data=[])

    knowledge_base_id = urllib.parse.unquote(knowledge_base_id)
    kb_path = get_kb_path(knowledge_base_id)
    local_doc_folder = get_doc_path(knowledge_base_id)
    if not os.path.exists(kb_path):
        return ListDocsResponse(
            code=404, msg=f"Knowledge base {knowledge_base_id} not found", data=[]
        )
    if not os.path.exists(local_doc_folder):
        all_doc_names = []
    else:
        all_doc_names = [
            doc
            for doc in os.listdir(local_doc_folder)
            if os.path.isfile(os.path.join(local_doc_folder, doc))
        ]
    return ListDocsResponse(data=all_doc_names)


async def delete_kb(
    knowledge_base_id: str = Query(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return BaseResponse(code=403, msg="Don't attack me")

    # TODO: 确认是否支持批量删除知识库
    knowledge_base_id = urllib.parse.unquote(knowledge_base_id)
    kb_path = get_kb_path(knowledge_base_id)
    if not os.path.exists(kb_path):
        return BaseResponse(
            code=404, msg=f"Knowledge base {knowledge_base_id} not found"
        )
    shutil.rmtree(kb_path)
    return BaseResponse(
        code=200, msg=f"Knowledge Base {knowledge_base_id} delete success"
    )


async def delete_doc(
    knowledge_base_id: str = Query(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    doc_name: str = Query(..., description="doc name", example="doc_name_1.pdf"),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return BaseResponse(code=403, msg="Don't attack me")

    knowledge_base_id = urllib.parse.unquote(knowledge_base_id)
    if not os.path.exists(get_kb_path(knowledge_base_id)):
        return BaseResponse(
            code=404, msg=f"Knowledge base {knowledge_base_id} not found"
        )
    doc_path = get_file_path(knowledge_base_id, doc_name)
    if os.path.exists(doc_path):
        os.remove(doc_path)
        remain_docs = await list_docs(knowledge_base_id)
        if len(remain_docs.data) == 0:
            shutil.rmtree(get_kb_path(knowledge_base_id), ignore_errors=True)
            return BaseResponse(code=200, msg=f"document {doc_name} delete success")
        else:
            status = local_doc_qa.delete_file_from_vector_store(
                doc_path, get_vs_path(knowledge_base_id)
            )
            if "success" in status:
                return BaseResponse(code=200, msg=f"document {doc_name} delete success")
            else:
                return BaseResponse(code=500, msg=f"document {doc_name} delete fail")
    else:
        return BaseResponse(code=404, msg=f"document {doc_name} not found")


async def update_doc(
    knowledge_base_id: str = Query(..., description="知识库名", example="kb1"),
    old_doc: str = Query(..., description="待删除文件名，已存储在知识库中", example="doc_name_1.pdf"),
    new_doc: UploadFile = File(description="待上传文件"),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    if not validate_kb_name(knowledge_base_id):
        return BaseResponse(code=403, msg="Don't attack me")

    knowledge_base_id = urllib.parse.unquote(knowledge_base_id)
    if not os.path.exists(get_kb_path(knowledge_base_id)):
        return BaseResponse(
            code=404, msg=f"Knowledge base {knowledge_base_id} not found"
        )
    doc_path = get_file_path(knowledge_base_id, old_doc)
    if not os.path.exists(doc_path):
        return BaseResponse(code=404, msg=f"document {old_doc} not found")
    else:
        os.remove(doc_path)
        delete_status = local_doc_qa.delete_file_from_vector_store(
            doc_path, get_vs_path(knowledge_base_id)
        )
        if "fail" in delete_status:
            return BaseResponse(code=500, msg=f"document {old_doc} delete failed")
        else:
            saved_path = get_doc_path(knowledge_base_id)
            if not os.path.exists(saved_path):
                os.makedirs(saved_path)

            file_content = await new_doc.read()  # 读取上传文件的内容

            file_path = os.path.join(saved_path, new_doc.filename)
            if os.path.exists(file_path) and os.path.getsize(file_path) == len(
                file_content
            ):
                file_status = f"document {new_doc.filename} already exists"
                return BaseResponse(code=200, msg=file_status)

            with open(file_path, "wb") as f:
                f.write(file_content)

            vs_path = get_vs_path(knowledge_base_id)
            vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(
                [file_path], vs_path
            )
            if len(loaded_files) > 0:
                file_status = f"document {old_doc} delete and document {new_doc.filename} upload success"
                return BaseResponse(code=200, msg=file_status)
            else:
                file_status = f"document {old_doc} success but document {new_doc.filename} upload fail"
                return BaseResponse(code=500, msg=file_status)


async def local_doc_chat(
    knowledge_base_id: str = Body(
        ..., description="Knowledge Base Name", example="kb1"
    ),
    question: str = Body(..., description="Question", example="工伤保险是什么？"),
    history: List[List[str]] = Body(
        [],
        description="History of previous questions and answers",
        example=[
            [
                "工伤保险是什么？",
                "工伤保险是指用人单位按照国家规定，为本单位的职工和用人单位的其他人员，缴纳工伤保险费，由保险机构按照国家规定的标准，给予工伤保险待遇的社会保险制度。",
            ]
        ],
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    vs_path = get_vs_path(knowledge_base_id)
    print(vs_path)
    if not os.path.exists(vs_path):
        # return BaseResponse(code=404, msg=f"Knowledge base {knowledge_base_id} not found")
        return ChatMessage(
            question=question,
            response=f"Knowledge base {knowledge_base_id} not found",
            history=history,
            source_documents=[],
        )
    else:
        for resp, history in local_doc_qa.get_knowledge_based_answer(
            query=question, vs_path=vs_path, chat_history=history, streaming=True
        ):
            pass
        source_documents = [
            f"""出处 [{inum + 1}] {os.path.split(doc.metadata['source'])[-1]}：\n\n{doc.page_content}\n\n"""
            f"""相关度：{doc.metadata['score']}\n\n"""
            for inum, doc in enumerate(resp["source_documents"])
        ]

        return ChatMessage(
            question=question,
            response=resp["result"],
            history=history,
            source_documents=source_documents,
        )


async def bing_search_chat(
    question: str = Body(..., description="Question", example="工伤保险是什么？"),
    history: Optional[List[List[str]]] = Body(
        [],
        description="History of previous questions and answers",
        example=[
            [
                "工伤保险是什么？",
                "工伤保险是指用人单位按照国家规定，为本单位的职工和用人单位的其他人员，缴纳工伤保险费，由保险机构按照国家规定的标准，给予工伤保险待遇的社会保险制度。",
            ]
        ],
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    for resp, history in local_doc_qa.get_search_result_based_answer(
        query=question, chat_history=history, streaming=True
    ):
        pass
    source_documents = [
        f"""出处 [{inum + 1}] [{doc.metadata["source"]}]({doc.metadata["source"]}) \n\n{doc.page_content}\n\n"""
        for inum, doc in enumerate(resp["source_documents"])
    ]

    return ChatMessage(
        question=question,
        response=resp["result"],
        history=history,
        source_documents=source_documents,
    )


async def chat(
    question: str = Body(..., description="Question", example="工伤保险是什么？"),
    history: Optional[List[List[str]]] = Body(
        [],
        description="History of previous questions and answers",
        example=[
            [
                "工伤保险是什么？",
                "工伤保险是指用人单位按照国家规定，为本单位的职工和用人单位的其他人员，缴纳工伤保险费，由保险机构按照国家规定的标准，给予工伤保险待遇的社会保险制度。",
            ]
        ],
    ),
    current_user: User = Depends(get_current_user),
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    answer_result_stream_result = local_doc_qa.llm_model_chain(
        {"prompt": question, "history": history, "streaming": True}
    )

    for answer_result in answer_result_stream_result["answer_result_stream"]:
        resp = answer_result.llm_output["answer"]
        history = answer_result.history
        pass
    return ChatMessage(
        question=question,
        response=resp,
        history=history,
        source_documents=[],
    )


async def stream_chat(
    websocket: WebSocket, current_user: User = Depends(get_current_user)
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    await websocket.accept()
    turn = 1
    while True:
        input_json = await websocket.receive_json()
        question, history, knowledge_base_id = (
            input_json["question"],
            input_json["history"],
            input_json["knowledge_base_id"],
        )
        vs_path = get_vs_path(knowledge_base_id)

        if not os.path.exists(vs_path):
            await websocket.send_json(
                {"error": f"Knowledge base {knowledge_base_id} not found"}
            )
            await websocket.close()
            return

        await websocket.send_json({"question": question, "turn": turn, "flag": "start"})

        last_print_len = 0
        for resp, history in local_doc_qa.get_knowledge_based_answer(
            query=question, vs_path=vs_path, chat_history=history, streaming=True
        ):
            await asyncio.sleep(0)
            await websocket.send_text(resp["result"][last_print_len:])
            last_print_len = len(resp["result"])

        source_documents = [
            f"""出处 [{inum + 1}] {os.path.split(doc.metadata['source'])[-1]}：\n\n{doc.page_content}\n\n"""
            f"""相关度：{doc.metadata['score']}\n\n"""
            for inum, doc in enumerate(resp["source_documents"])
        ]

        await websocket.send_text(
            json.dumps(
                {
                    "question": question,
                    "turn": turn,
                    "flag": "end",
                    "sources_documents": source_documents,
                },
                ensure_ascii=False,
            )
        )
        turn += 1


async def stream_chat_bing(
    websocket: WebSocket, current_user: User = Depends(get_current_user)
):
    # 登录拦截
    if not current_user:
        raise credentials_exception
    """
    基于bing搜索的流式问答
    """
    await websocket.accept()
    turn = 1
    while True:
        input_json = await websocket.receive_json()
        question, history = input_json["question"], input_json["history"]

        await websocket.send_json({"question": question, "turn": turn, "flag": "start"})

        last_print_len = 0
        for resp, history in local_doc_qa.get_search_result_based_answer(
            question, chat_history=history, streaming=True
        ):
            await websocket.send_text(resp["result"][last_print_len:])
            last_print_len = len(resp["result"])

        source_documents = [
            f"""出处 [{inum + 1}] {os.path.split(doc.metadata['source'])[-1]}：\n\n{doc.page_content}\n\n"""
            f"""相关度：{doc.metadata['score']}\n\n"""
            for inum, doc in enumerate(resp["source_documents"])
        ]

        await websocket.send_text(
            json.dumps(
                {
                    "question": question,
                    "turn": turn,
                    "flag": "end",
                    "sources_documents": source_documents,
                },
                ensure_ascii=False,
            )
        )
        turn += 1


async def document():
    return RedirectResponse(url="/docs")


def api_start(host, port, **kwargs):
    global app
    global local_doc_qa

    llm_model_ins = shared.loaderLLM()

    # app = FastAPI()
    # Add CORS middleware to allow all origins
    # 在config.py中设置OPEN_DOMAIN=True，允许跨域
    # set OPEN_DOMAIN=True in config.py to allow cross-domain
    if OPEN_CROSS_DOMAIN:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    # 修改了stream_chat的接口，直接通过ws://localhost:7861/local_doc_qa/stream_chat建立连接，在请求体中选择knowledge_base_id
    app.websocket("/local_doc_qa/stream_chat")(stream_chat)

    app.get("/", response_model=BaseResponse, summary="swagger 文档")(document)

    # 增加基于bing搜索的流式问答
    # 需要说明的是，如果想测试websocket的流式问答，需要使用支持websocket的测试工具，如postman,insomnia
    # 强烈推荐开源的insomnia
    # 在测试时选择new websocket request,并将url的协议改为ws,如ws://localhost:7861/local_doc_qa/stream_chat_bing
    app.websocket("/local_doc_qa/stream_chat_bing")(stream_chat_bing)

    app.post("/chat", response_model=ChatMessage, summary="与模型对话")(chat)

    app.post(
        "/local_doc_qa/upload_file", response_model=BaseResponse, summary="上传文件到知识库"
    )(upload_file)
    app.post(
        "/local_doc_qa/upload_files", response_model=BaseResponse, summary="批量上传文件到知识库"
    )(upload_files)
    app.post(
        "/local_doc_qa/local_doc_chat", response_model=ChatMessage, summary="与知识库对话"
    )(local_doc_chat)
    app.post(
        "/local_doc_qa/bing_search_chat", response_model=ChatMessage, summary="与必应搜索对话"
    )(bing_search_chat)
    app.get(
        "/local_doc_qa/list_knowledge_base",
        response_model=ListDocsResponse,
        summary="获取知识库列表",
    )(list_kbs)
    app.get(
        "/local_doc_qa/list_files",
        response_model=ListDocsResponse,
        summary="获取知识库内的文件列表",
    )(list_docs)
    app.delete(
        "/local_doc_qa/delete_knowledge_base",
        response_model=BaseResponse,
        summary="删除知识库",
    )(delete_kb)
    app.delete(
        "/local_doc_qa/delete_file", response_model=BaseResponse, summary="删除知识库内的文件"
    )(delete_doc)
    app.post(
        "/local_doc_qa/update_file",
        response_model=BaseResponse,
        summary="上传文件到知识库，并删除另一个文件",
    )(update_doc)

    local_doc_qa = LocalDocQA()
    local_doc_qa.init_cfg(
        llm_model=llm_model_ins,
        embedding_model=EMBEDDING_MODEL,
        embedding_device=EMBEDDING_DEVICE,
        top_k=VECTOR_SEARCH_TOP_K,
    )
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_keyfile=kwargs.get("ssl_keyfile"),
            ssl_certfile=kwargs.get("ssl_certfile"),
        )
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = None
    args = parser.parse_args()
    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    api_start(
        args.host,
        args.port,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
    )
