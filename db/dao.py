import mysql.connector
from passlib.context import CryptContext

from pojo.Message import Message
from pojo.UserInDB import UserInDB
from pojo.Conversation import Conversation

# 配置数据库连接
db_config = {
    "host": "xxxxxx",
    "user": "xxx",
    "password": "xxx",
    "database": "chatga",
}

# 配置密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


db_conn = mysql.connector.connect(**db_config)
db_cursor = db_conn.cursor()


######----------------t_user-------------------########
# 查询用户
def get_user(username):
    sql = "SELECT * FROM t_user WHERE username=%s"
    db_cursor.execute(sql, (username,))
    user = db_cursor.fetchone()
    if not user:
        return None
    return UserInDB(user_id=user[0], username=user[1], hashed_password=user[2])

# 验证用户
def authenticate_user(username: str, password: str):
    userInDB = get_user(username)
    if not userInDB:
        return False
    elif not pwd_context.verify(password, userInDB.hashed_password):
        return False
    return userInDB

# 创建用户
def create_user(username: str, password: str):
    # 哈希处理密码
    hashed_password = pwd_context.hash(password)

    # 插入用户数据
    sql = "INSERT INTO t_user (username, password, create_time) VALUES (%s, %s, NOW())"
    db_cursor.execute(sql, (username, hashed_password))
    db_conn.commit()


#########----------------t_conversation-------------------#########

# 分页获取用户的会话，并根据更新时间进行排序, 进行ORM映射
def get_conversations_by_user_id_with_orm(user_id: int, offset: int = 0, limit: int = 28, order: str = "updated"):
    # 根据更新时间进行排序
    if order == "updated":
        sql = "SELECT * FROM t_conversation WHERE user_id=%s ORDER BY update_time DESC LIMIT %s, %s"
    else:
        sql = "SELECT * FROM t_conversation WHERE user_id=%s ORDER BY conv_id DESC LIMIT %s, %s"
    db_cursor.execute(sql, (user_id, offset, limit))
    conversations = db_cursor.fetchall()
    # ORM映射为Conversation对象
    conversations = [Conversation(conv_id=conv[0], user_id=conv[1], title=conv[2], create_time=conv[3], update_time=conv[4]) for conv in conversations]
    return conversations

# 点击创建会话，title默认值为"新的对话"
def create_conversation(user_id: int):
    sql = "INSERT INTO t_conversation (user_id, title, create_time, update_time) VALUES (%s, %s, NOW(), NOW())"
    db_cursor.execute(sql, (user_id, "新的对话"))
    db_conn.commit()
    return db_cursor.lastrowid

# 更新会话
def update_conversation(conv_id: int, title: str):
    sql = "UPDATE t_conversation SET title=%s, update_time=NOW() WHERE conv_id=%s"
    db_cursor.execute(sql, (title, conv_id))
    db_conn.commit()

# 删除会话
def delete_conversation(conv_id: int):
    sql = "DELETE FROM t_conversation WHERE conv_id=%s"
    db_cursor.execute(sql, (conv_id,))
    db_conn.commit()



##########----------------t_message-------------------#########


# 根据会话id获取会话信息，并根据创建时间进行排序，最后进行ORM映射
def get_messages_by_conv_id_with_orm(conv_id: int):
    sql = "SELECT * FROM t_message WHERE conv_id=%s ORDER BY create_time"
    db_cursor.execute(sql, (conv_id,))
    messages = db_cursor.fetchall()
    # print(messages)
    # ORM映射为Message对象
    messages = [Message(msg_id=msg[0], conv_id=msg[1], role=msg[2], content=msg[3], content_type=msg[4], create_time=msg[5]) for msg in messages]
    return messages

# 创建消息
def create_message(conv_id: int, role: str, content: str, content_type: str):
    sql = "INSERT INTO t_message (conv_id, role, content, content_type, create_time) VALUES (%s, %s, %s, %s, NOW())"
    db_cursor.execute(sql, (conv_id, role, content, content_type))
    db_conn.commit()
    return db_cursor.lastrowid

