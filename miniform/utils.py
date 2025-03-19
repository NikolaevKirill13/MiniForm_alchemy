import bcrypt

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


def get_class_name_with_table_name(name: str):
    def find_class(cls):
        if hasattr(cls, "__tablename__") and cls.__tablename__ == name:
            return cls
        for sub_cls in cls.__subclasses__():
            result = find_class(sub_cls)
            if result:
                return result
        return None

    result = find_class(DeclarativeBase)
    if not result:
        raise ValueError(f'The class with table name "{name}" not found.')
    return result


def hashed_func(value):
    password = str(value).encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    return hashed_password.decode("utf-8")


def check_hash(input_password, hashed_password):
    input_password = str(input_password).encode("utf-8")
    hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(input_password, hashed_password)


__all__ = ('hashed_func', 'check_hash')