from server.db.models.message_model import MessageModel
from server.db.session import with_session

# 根据会话id获取会话信息，并根据创建时间排序
@with_session
def get_messages(session, conv_id: int, page: int = 1, page_size: int = 10):
    messages = session.query(MessageModel).filter_by(conv_id=conv_id).order_by(
        MessageModel.create_time.desc()).limit(page_size).offset((page - 1) * page_size).all()
    # 返回MessageModel的所有内容，以json字符串的形式
    messages = ["{'conv_id': %d, 'role': '%s', 'content': '%s', 'content_type': '%s'}" % (message.conv_id, message.role, message.content, message.content_type)
    for message in messages]
    return messages

# 创建消息
@with_session
def create_message(session, conv_id: int, role: str, content: str, content_type: str):
    message = MessageModel(conv_id=conv_id, role=role, content=content, content_type=content_type)
    session.add(message)
    return True

# 根据会话id删除所有其中的消息
@with_session
def delete_messages(session, conv_id: int):
    messages = session.query(MessageModel).filter_by(conv_id=conv_id).all()
    for message in messages:
        session.delete(message)
    return True
