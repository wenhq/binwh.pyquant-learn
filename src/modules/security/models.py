# database/models/user.py
class User:
    """用户数据模型"""
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
