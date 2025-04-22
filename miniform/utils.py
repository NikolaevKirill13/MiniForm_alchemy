from typing import Union

import bcrypt

from sqlalchemy.orm import DeclarativeBase


def get_class_name_with_table_name(name: str):
    """
    Возвращает класс по имени таблицы.

    Args:
        name: имя таблицы

    Returns:
        класс
    """

    def find_class(cls):
        """
        Ищет класс по имени таблицы.

        Args:
            cls:

        Returns:

        """
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


def hashed_func(value: Union[str, int, float]):
    """
    Функция для шифрования паролей.

    Args:
        value: значение для шифрования

    Returns:
        str
    """
    password = str(value).encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    return hashed_password.decode("utf-8")


def check_hash(input_password: str, hashed_password: str) -> bool:
    """
    Функция проверки пароля

    Args:
        input_password: пароль для проверки.
        hashed_password: валидное значение из базы данных.

    Returns:
        bool
    """
    input_password = str(input_password).encode("utf-8")
    hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(input_password, hashed_password)


__all__ = ('hashed_func', 'check_hash', 'get_class_name_with_table_name')