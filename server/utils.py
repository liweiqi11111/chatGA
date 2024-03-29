import pydantic
from pydantic import BaseModel
from typing import List
import torch
from fastapi import FastAPI
from pathlib import Path
import asyncio
from typing import Any, Optional


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

class ListResponse(BaseResponse):
    data: List[str] = pydantic.Field(..., description="List of names")

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
                "data": ["doc1.docx", "doc2.pdf", "doc3.txt"],
            }
        }

class ConversationResponse(BaseResponse):
    # 这里会报错，pydantic不支持嵌套的List[dict]类型,
    data: List[dict] = pydantic.Field(..., description="List of conversations")
    
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
    data: List[dict] = pydantic.Field(..., description="List of messages")
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
                "response": "根据已知信息，可以总结如下：\n\n1. 参保单位为员工缴纳工伤保险费，以保障员工在发生工伤时能够获得相应的待遇。\n"
                            "2. 不同地区的工伤保险缴费规定可能有所不同，需要向当地社保部门咨询以了解具体的缴费标准和规定。\n"
                            "3. 工伤从业人员及其近亲属需要申请工伤认定，确认享受的待遇资格，并按时缴纳工伤保险费。\n"
                            "4. 工伤保险待遇包括工伤医疗、康复、辅助器具配置费用、伤残待遇、工亡待遇、一次性工亡补助金等。\n"
                            "5. 工伤保险待遇领取资格认证包括长期待遇领取人员认证和一次性待遇领取人员认证。\n"
                            "6. 工伤保险基金支付的待遇项目包括工伤医疗待遇、康复待遇、辅助器具配置费用、一次性工亡补助金、丧葬补助金等。",
                "history": [
                    [
                        "工伤保险是什么？",
                        "工伤保险是指用人单位按照国家规定，为本单位的职工和用人单位的其他人员，缴纳工伤保险费，"
                        "由保险机构按照国家规定的标准，给予工伤保险待遇的社会保险制度。",
                    ]
                ],
                "source_documents": [
                    "出处 [1] 广州市单位从业的特定人员参加工伤保险办事指引.docx：\n\n\t"
                    "( 一)  从业单位  (组织)  按“自愿参保”原则，  为未建 立劳动关系的特定从业人员单项参加工伤保险 、缴纳工伤保 险费。",
                    "出处 [2] ...",
                    "出处 [3] ...",
                ],
            }
        }

def torch_gc():
    if torch.cuda.is_available():
        # with torch.cuda.device(DEVICE):
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    elif torch.backends.mps.is_available():
        try:
            from torch.mps import empty_cache
            empty_cache()
        except Exception as e:
            print(e)
            print("如果您使用的是 macOS 建议将 pytorch 版本升级至 2.0.0 或更高版本，以支持及时清理 torch 产生的内存占用。")


def run_async(cor):
    '''
    在同步环境中运行异步代码.
    '''
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
    return loop.run_until_complete(cor)


def iter_over_async(ait, loop):
    '''
    将异步生成器封装成同步生成器.
    '''
    ait = ait.__aiter__()
    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj


def MakeFastAPIOffline(
    app: FastAPI,
    static_dir = Path(__file__).parent / "static",
    static_url = "/static-offline-docs",
    docs_url: Optional[str] = "/docs",
    redoc_url: Optional[str] = "/redoc",
) -> None:
    """patch the FastAPI obj that doesn't rely on CDN for the documentation page"""
    from fastapi import Request
    from fastapi.openapi.docs import (
        get_redoc_html,
        get_swagger_ui_html,
        get_swagger_ui_oauth2_redirect_html,
    )
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import HTMLResponse

    openapi_url = app.openapi_url
    swagger_ui_oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url

    def remove_route(url: str) -> None:
        '''
        remove original route from app
        '''
        index = None
        for i, r in enumerate(app.routes):
            if r.path.lower() == url.lower():
                index = i
                break
        if isinstance(index, int):
            app.routes.pop(i)

    # Set up static file mount
    app.mount(
        static_url,
        StaticFiles(directory=Path(static_dir).as_posix()),
        name="static-offline-docs",
    )

    if docs_url is not None:
        remove_route(docs_url)
        remove_route(swagger_ui_oauth2_redirect_url)

        # Define the doc and redoc pages, pointing at the right files
        @app.get(docs_url, include_in_schema=False)
        async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"
            return get_swagger_ui_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
                swagger_js_url=f"{root}{static_url}/swagger-ui-bundle.js",
                swagger_css_url=f"{root}{static_url}/swagger-ui.css",
                swagger_favicon_url=favicon,
            )

        @app.get(swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect() -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()

    if redoc_url is not None:
        remove_route(redoc_url)

        @app.get(redoc_url, include_in_schema=False)
        async def redoc_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"

            return get_redoc_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - ReDoc",
                redoc_js_url=f"{root}{static_url}/redoc.standalone.js",
                with_google_fonts=False,
                redoc_favicon_url=favicon,
            )
