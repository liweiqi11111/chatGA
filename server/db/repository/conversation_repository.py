from server.db.models.conversation_model import ConversationModel
from server.db.session import with_session

# 分页获取用户的会话，并根据更新时间进行排序，最新的会话排在最前面
@with_session
def get_conversations(session, user_id: int, page: int = 1, page_size: int = 10):
    conversations = session.query(ConversationModel).filter_by(user_id=user_id).order_by(
        ConversationModel.update_time.desc()).limit(page_size).offset((page - 1) * page_size).all()
    return conversations

# 创建会话，title默认为“新的会话”
@with_session
def create_conversation(session, user_id: int):
    conversation = ConversationModel(user_id=user_id, title="新的会话")
    session.add(conversation)
    return True

# 更新会话的title并保存回数据库
@with_session
def update_conversation_title(session, conv_id: int, title: str):
    conversation = session.query(ConversationModel).filter_by(conv_id=conv_id).first()
    if conversation:
        conversation.title = title
    return True

# 删除会话, 会话删除后，会话下的消息也会被删除
# 如果会话不存在，返回False
@with_session
def delete_conversation(session, conv_id: int):
    conversation = session.query(ConversationModel).filter_by(conv_id=conv_id).first()
    if conversation:
        session.delete(conversation)
        return True
    return False