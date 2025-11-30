"""SQLAlchemy基类和共享配置"""
from sqlalchemy.orm import DeclarativeBase, declarative_base


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


# 兼容性别名
BaseModel = Base
