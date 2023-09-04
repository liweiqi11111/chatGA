import nltk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from configs.model_config import NLTK_DATA_PATH
from configs.server_config import OPEN_CROSS_DOMAIN
from configs import VERSION
import argparse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from server.information.information_api import (login_for_access_token, register,
                                                get_conversations, get_messages, create_conversation,
                                                update_conversation, delete_conversation, 
                                                create_message)
from server.chat import (chat, knowledge_base_chat, openai_chat,
                         search_engine_chat)
from server.knowledge_base.kb_api import list_kbs, create_kb, delete_kb
from server.knowledge_base.kb_doc_api import (list_docs, upload_doc, delete_doc,
                                              update_doc, download_doc, recreate_vector_store,
                                              search_docs, DocumentWithScore)
from server.utils import BaseResponse, ListResponse, FastAPI, MakeFastAPIOffline
from typing import List

nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path


async def document():
    return RedirectResponse(url="/docs")


def create_app():
    app = FastAPI(
        title="Langchain-Chatchat API Server",
        version=VERSION
    )
    MakeFastAPIOffline(app)
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

    # 创建中间件，对除登录和注册的所有请求进行token验证
    # Create middleware to verify token for all requests except login and register
    from server.information.information_api import get_current_user
    from server.information.information_api import credentials_exception
    from jose import JWTError

    @app.middleware("http")
    async def auth_middleware(request, call_next):
        if request.url.path not in ["/login", "/register"]:
            token = request.headers["Authorization"].split(" ")[1]
            try:
                user = await get_current_user(token)
            except JWTError:
                raise credentials_exception
        response = await call_next(request)
        return response


    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    # Tag: Information
    app.post("/login", 
                tags=["Information"],
                summary="用户登录")(login_for_access_token)
    
    app.post("/register", 
                tags=["Information"],
                summary="用户注册")(register)
    
    app.get("/conversations",
            tags=["Information"],
            response_model=ListResponse,
            summary="获取会话列表")(get_conversations)

    app.get("/conversation",
            tags=["Information"],
            summary="根据conv_id获取会话中的所有消息")(get_messages)

    app.post("/conversation",
             tags=["Information"],
             summary="创建会话")(create_conversation)

    app.put("/conversation",
            tags=["Information"],
            summary="更新会话")(update_conversation)

    app.delete("/conversation",
            tags=["Information"],
            summary="删除会话")(delete_conversation)            

    app.post("/message",
            tags=["Information"],
            summary="创建消息")(create_message)
    


    # Tag: Chat
    app.post("/chat/fastchat",
             tags=["Chat"],
             summary="与llm模型对话(直接与fastchat api对话)")(openai_chat)

    app.post("/chat/chat",
             tags=["Chat"],
             summary="与llm模型对话(通过LLMChain)")(chat)

    app.post("/chat/knowledge_base_chat",
             tags=["Chat"],
             summary="与知识库对话")(knowledge_base_chat)

    app.post("/chat/search_engine_chat",
             tags=["Chat"],
             summary="与搜索引擎对话")(search_engine_chat)

    # Tag: Knowledge Base Management
    app.get("/knowledge_base/list_knowledge_bases",
            tags=["Knowledge Base Management"],
            response_model=ListResponse,
            summary="获取知识库列表")(list_kbs)

    app.post("/knowledge_base/create_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="创建知识库"
             )(create_kb)

    app.post("/knowledge_base/delete_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库"
             )(delete_kb)

    app.get("/knowledge_base/list_docs",
            tags=["Knowledge Base Management"],
            response_model=ListResponse,
            summary="获取知识库内的文件列表"
            )(list_docs)

    app.post("/knowledge_base/search_docs",
             tags=["Knowledge Base Management"],
             response_model=List[DocumentWithScore],
             summary="搜索知识库"
             )(search_docs)

    app.post("/knowledge_base/upload_doc",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="上传文件到知识库"
             )(upload_doc)

    app.post("/knowledge_base/delete_doc",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库内指定文件"
             )(delete_doc)

    app.post("/knowledge_base/update_doc",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="更新现有文件到知识库"
             )(update_doc)

    app.get("/knowledge_base/download_doc",
            tags=["Knowledge Base Management"],
            summary="下载对应的知识文件")(download_doc)

    app.post("/knowledge_base/recreate_vector_store",
             tags=["Knowledge Base Management"],
             summary="根据content中文档重建向量库，流式输出处理进度。"
             )(recreate_vector_store)

    return app


app = create_app()


def run_api(host, port, **kwargs):
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(app,
                    host=host,
                    port=port,
                    ssl_keyfile=kwargs.get("ssl_keyfile"),
                    ssl_certfile=kwargs.get("ssl_certfile"),
                    )
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='langchain-ChatGLM',
                                     description='About langchain-ChatGLM, local knowledge based ChatGLM with langchain'
                                                 ' ｜ 基于本地知识库的 ChatGLM 问答')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7863)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)
    run_api(host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
