import os
import re

from sqlalchemy import Dialect
from sqlalchemy.types import TypeDecorator, String
from typing import Any, Union, Dict

from miniform.utils import hashed_func


class FileField(TypeDecorator):
    impl = String
    model_type = "FileField"

    def __init__(
            self,
            upload_to: str,
            max_size: int,
            allowed_extensions: list = None,
            file_is_empty: bool = False,
            name_translate: bool = False,
            *args,
            **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.upload_to = upload_to
        self.max_size = abs(max_size) * 1024
        self.file_is_empty = file_is_empty
        self._existing_value = None
        self.name_translate = name_translate

        self.allowed_extensions = []
        if allowed_extensions:
            for ext in allowed_extensions:
                ext = ext.lower().strip()
                if not ext.startswith("."):
                    ext = f".{ext}"
                self.allowed_extensions.append(ext)
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def set_existing_value(self, value: str) -> None:
        """
        Метод для установки существующего значения
        :param value: str
        :return: None
        """
        self._existing_value = value

    def create_directory(self) -> None:
        """
        Метод создания директории для загрузки файлов.
        :return: None
        """
        if not os.path.exists(self.upload_to):
            os.makedirs(self.upload_to)

    @staticmethod
    def russian_to_english(text):
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        result = []
        for char in text:
            if char in translit_dict:
                result.append(translit_dict[char])
            else:
                result.append(char)
        return ''.join(result)

    def process_bind_param(self, value, dialect) -> Union[str, None]:
        if value is None or (value.size == 0 and value.filename == ""):
            return (
                    self._existing_value or ""
            )  # Возвращаем существующее значение или пустую строку
        if value.size == 0 and self.file_is_empty is False:
            raise ValueError("File must be not empty")
        if value.size == 0 and self.file_is_empty:
            return ""
        if value.size > self.max_size:
            raise ValueError(f"File size exceeds maximum allowed {self.max_size / 1024}KB")
        self.create_directory()  # Убеждаемся, что каталог создан
        if self.name_translate:
            # Заменим русские буквы на английские
            value.filename = self.russian_to_english(value.filename)
            # Проверка имени файла и его расширения
        filename = self.validate_filename(unquote(value.filename))
        # Генерация пути для сохранения файла
        filepath = self.get_unique_filepath(filename)
        # удаляем старый файл
        if self._existing_value and os.path.exists(self._existing_value):
            os.remove(self._existing_value)
        with open(filepath, "wb") as f:
            content = value.file.read()  # Читаем содержимое файла
            f.write(content)
            # Обновляем существующее значение на новый путь
        self.set_existing_value(os.path.relpath(filepath))
        return os.path.relpath(filepath)  # Возвращаем относительный путь к файлу

    def validate_filename(self, filename: str) -> str:
        filename = os.path.basename(filename)  # Удаляем пути
        name_part, ext_part = os.path.splitext(filename)
        ext_part = ext_part.lower().strip()  # Приводим к нижнему регистру и убираем пробелы
        # Если имя файла начинается с точки (например, ".txt")
        if name_part.startswith(".") and not ext_part:
            # Переставляем части: name_part = "", ext_part = ".txt"
            name_part, ext_part = "", name_part.lower()
        # Если имя файла пустое (например, ".txt" → name_part="", ext_part=".txt")
        if not name_part.strip():
            name_part = "1"
        # Проверка наличия расширения
        if not ext_part:
            raise ValueError("File must have an extension")
        # Проверка разрешенных расширений
        if ext_part not in self.allowed_extensions:
            raise ValueError(f"File type '{ext_part}' is not allowed")
        return f"{name_part}{ext_part}"

    def get_unique_filepath(self, filename: str) -> str:
        clean_name = re.sub(r"[^\w\-.]", "", filename.replace(" ", "_"))
        filepath = os.path.join(self.upload_to, clean_name)
        if not clean_name.strip("._-"):
            clean_name = "file" + (f".{extension}" if (extension := os.path.splitext(filename)[1]) else "")
            filepath = os.path.join(self.upload_to, clean_name)
        base, extension = os.path.splitext(clean_name)
        counter = 2
        while os.path.exists(filepath):
            new_filename = f"{base}({counter}){extension}"
            filepath = os.path.join(self.upload_to, new_filename)
            counter += 1
        return filepath

    def process_result_value(self, value: Any, dialect) -> Any:
        return value if value else ""  # Возвращаем относительный путь


class ImageField(FileField):
    impl = String
    model_type = "ImageField"

    def __init__(
            self,
            upload_to: str,
            max_size: int,
            allowed_extensions: list = None,
            file_is_empty: bool = False,
            *args,
            **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.upload_to = upload_to
        self.max_size = abs(max_size) * 1024
        self.file_is_empty = file_is_empty
        self._existing_value = None

        self.allowed_extensions = []
        if allowed_extensions:
            for ext in allowed_extensions:
                ext = ext.lower().strip()
                if not ext.startswith("."):
                    ext = f".{ext}"
                self.allowed_extensions.append(ext)
        else:
            self.allowed_extensions.append(".image/*")
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)


class PasswordField(TypeDecorator):
    impl = String

    def __init__(self, max_length: int = None, min_length: int = None, func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = hashed_func if func is None else func
        self.max_length = abs(max_length) if max_length else 256
        self.min_length = abs(min_length) if min_length else 0

    def process_bind_param(self, value, dialect: Dialect) -> Any:
        if value is None:
            return None
        if len(value) > self.max_length:
            raise ValueError(f"Maximum password length {self.max_length} characters")
        if len(value) < self.min_length:
            raise ValueError(f"Minimum password length {self.max_length} characters")
        return self.func(value)

    def process_result_value(self, value, dialect: Dialect):
        return value if value else ""


__all__ = ('FileField', 'ImageField', 'PasswordField')