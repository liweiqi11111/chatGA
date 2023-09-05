from server.information.User import User
from server.db.repository.userInDB_repository import (
    get_user, authenticate_user, create_user)

from server.db.repository.conversation_repository import (
    get_conversations, create_conversation, update_conversation_title, delete_conversation)

from server.db.repository.message_repository import (
    get_messages, create_message, delete_messages)


class InformationService():
    
    def get_user(self, username: str):
        user = get_user(username)
        if not user:
            return False
        return self.convert_userDB_to_User(user)
    
    def authenticate_user(self, username: str, password: str):
        status = authenticate_user(username, password)
        return status
    
    def create_user(self, username: str, password: str):
        status = create_user(username, password)
        return status
    
    def get_conversations(self, user_id: int, page: int = 1, page_size: int = 10):
        conversations = get_conversations(user_id, page, page_size)
        return conversations
    
    def create_conversation(self, user_id: int):
        status = create_conversation(user_id)
        return status
    
    def delete_conversation(self, conv_id: int):
        # 删除会话，会话下的消息也会被删除
        status = delete_conversation(conv_id)
        if status:
            status = delete_messages(conv_id)
        return status
    
    def update_conversation_title(self, conv_id: int, title: str):
        status = update_conversation_title(conv_id, title)
        return status
    
    def get_messages(self, conv_id: int):
        messages = get_messages(conv_id)
        return messages
    
    def create_message(self, conv_id: int, role: str, content: str, content_type: str):
        status = create_message(conv_id, role, content, content_type)
        return status
    

    def convert_userDB_to_User(self, user):
        return User(user_id=user.user_id, username=user.username)
