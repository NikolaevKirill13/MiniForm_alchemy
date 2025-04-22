import re
from abc import abstractmethod
from datetime import datetime, date, time
from functools import wraps
from importlib import import_module
from typing import Union, Dict, Any, Optional, Type, Callable, TypedDict
import nest_asyncio
from markupsafe import Markup, escape

from sqlalchemy.orm import DeclarativeBase


class TextWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для TextWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - autocomplete: str - Автодополнение поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
    """
    title: str
    placeholder: str
    autocomplete: str
    maxlength: int
    minlength: int


class TextAreaWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для TextAreaWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - autocomplete: str - Автодополнение поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
    """
    title: str
    placeholder: str
    autocomplete: str
    maxlength: int
    minlength: int


class EmailWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для EmailWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - autocomplete: str - Автодополнение поля.
    """
    title: str
    placeholder: str
    autocomplete: str


class IntegerWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для IntegerWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
        - max: int - Максимальное значение поля.
        - min: int - Минимальное значение поля.
    """
    title: str
    placeholder: str
    maxlength: int
    minlength: int
    max: int
    min: int


class FloatWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для FloatWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
        - max: float - Максимальное значение поля.
        - min: float - Минимальное значение поля.
        - step: float - Шаг значения поля.
    """
    title: str
    placeholder: str
    maxlength: int
    minlength: int
    max: float
    min: float
    step: float


class RangeWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для RangeWidget :
        - title: str - Текст подсказки поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
        - max: float - Максимальное значение поля.
        - min: float - Минимальное значение поля.
        - step: float - Шаг значения поля
    """
    title: str
    maxlength: int
    minlength: int
    min: float
    max: float
    step: float


class PasswordWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для PasswordWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - autocomplete: str - Автодополнение поля.
        - maxlength: int - Максимальная длинна значения.
        - minlength: int - Минимальная длинна значения.
    """
    title: str
    placeholder: str
    autocomplete: str
    maxlength: int
    minlength: int
    autocomplete: str


class TimeWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для TimeWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - max: time - Максимальное значение поля.
        - min: time - Минимальное значение поля.
    """
    title: str
    placeholder: str
    max: time
    min: time


class DateWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для DateWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - max: date - Максимальное значение поля.
        - min: date - Минимальное значение поля.
    """
    title: str
    placeholder: str
    max: date
    min: date


class DateTimeWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для DateTimeWidget :
        - title: str - Текст подсказки поля.
        - placeholder: str - Текст-пример для поля.
        - max: datetime - Максимальное значение поля.
        - min: datetime - Минимальное значение поля.
    """
    title: str
    placeholder: str
    max: datetime
    min: datetime


class SelectWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для SelectWidget :
        - title: str - Текст подсказки поля.
        - options: dict - Словарь.
    """
    title: str
    options: dict


class CheckBoxWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для CheckBoxWidgetWidget :
        - title: str - Текст подсказки поля.
    """
    title: str


class FileWidgetExtraAttrs(TypedDict, total=False):
    """
    Словарь дополнительных атрибутов для FileWidgetWidgetWidget :
        - title: str - Текст подсказки поля.
    """
    title: str


ExtraAttrsDict = Union[
    TextWidgetExtraAttrs,
    TextAreaWidgetExtraAttrs,
    EmailWidgetExtraAttrs,
    IntegerWidgetExtraAttrs,
    FloatWidgetExtraAttrs,
    RangeWidgetExtraAttrs,
    PasswordWidgetExtraAttrs,
    TimeWidgetExtraAttrs,
    DateWidgetExtraAttrs,
    DateTimeWidgetExtraAttrs,
    SelectWidgetExtraAttrs,
    CheckBoxWidgetExtraAttrs,
    FileWidgetExtraAttrs
]


class AbstractWidget:
    type: str = None
    pattern: str = None
    value_type: Optional[Type[Any]] = None
    list_error: list = None

    def __init__(
            self,
            name: str = None,
            label: str = None,
            readonly: bool = False,
            hidden: bool = False,
            required: bool = False,
            disabled: bool = False,
            extra_attrs: dict = None,
            init_data: Union[dict[Union[str, int], Optional[Any]]] = None,
            options: Union[dict[str, Union[str, int]], dict[int, Union[str, int]]] = None,
            extensions: str = None,
            prefix: str = None,
            validator: Callable = None,
    ):
        self.name = name or None  #
        self.label_name = label
        self.hidden = hidden or False
        self.readonly = readonly or False
        self.required = required or False
        self.disabled = disabled or False
        self.extra_attrs = extra_attrs or {}  #
        self.init_data = init_data or {}  #
        self.options = options or {}
        self.extensions = extensions or None
        self.prefix = prefix or None
        self.default_validator = validator or self.default_validator  #

    def __set_name__(self, owner, name):
        self.name = name

    def get_structure_extra_attrs(self):
        pass

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @abstractmethod
    def default_validator(self, value):
        raise NotImplementedError

    @abstractmethod
    def get_label(self):
        raise NotImplementedError

    @abstractmethod
    def get_input(self):
        raise NotImplementedError

    @abstractmethod
    def update_attrs(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def update_attrs2(
            self,
            extra_attrs=None,
            obj=None,
            prefix=None,
            options=None,
    ):
        raise NotImplementedError

    @abstractmethod
    def convert(self, value):
        raise NotImplementedError


class BaseWidget(AbstractWidget):

    @wraps(AbstractWidget.__init__)
    def __init__(self, *args, **kwargs):
        nest_asyncio.apply()
        super().__init__(*args, **kwargs)
        self.label_field = self.get_label()
        self.field = self.get_input()

    def __str__(self):
        return str(self.__html__())

    def __html__(self):
        field_hidden = " hidden" if self.hidden is True else ""
        self.error = self.get_error()
        return Markup(
            f'<div class="form-group"{field_hidden}>\n'
            f"{self.label_field}"
            f"{self.field}"
            f"{self.error}"
            "</div>\n"
        )

    def get_error(self):
        if self.list_error:
            return Markup("").join(
                Markup(f' <small class="error">error: {escape(value_error)}</small>\n')
                for value_error in self.list_error
            )
        return ""

    def get_data_to_dict(self):
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.get_widget_prefix(),
                    "value": list(self.init_data.values())[0] if self.init_data else "",
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": list(self.init_data.values())[0],
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict

    def get_widget_prefix(self):
        if self.prefix:
            return self.prefix + "_" + self.name
        return self.name

    def get_init_value(self) -> str:
        safe_values = [
            f' value="{escape(str(value))}"'
            for key, value in self.init_data.items()
            if self.init_data and key == self.name and value not in ("", "None")
        ]
        return "".join(safe_values)

    def get_widget_attrs(self) -> str:
        attrs = (
                (" readonly" if self.readonly else "")
                + (" required" if self.required else "")
                + (" disabled" if self.disabled else "")
        )
        return attrs

    def get_label(self) -> str:
        value = self.get_widget_prefix()
        return Markup(f'<label for="{value}">{escape(self.label_name)}</label>\n')

    def get_extra_attrs(self) -> str:
        """
        Метод возвращающий строковое представление дополнительных атрибутов поля.
        Returns:
            str
        """
        return "".join(
            f' {key}="{value}"'
            for key, value in self.extra_attrs.items()
            if self.extra_attrs != {}
            if value != ""
        )

    def get_input(self) -> Markup:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        init_value = self.get_init_value()
        extra_attrs = self.get_extra_attrs()
        return (
                Markup(
                    f'<input type="{self.type}" name="{value}" id="{value}"'
                    f"{attrs}{init_value}{extra_attrs} />"
                )
                + html_icon
                + Markup("<br>\n")
        )

    def update_attrs(self,
                     extra_attrs: Union[dict[str, str], dict[str, int], dict[str, float], None] = None,
                     obj: Union[
                         dict[str, str], dict[int, str], dict[int, int], dict[str, int]
                     ] = None,
                     prefix=None,
                     options: Union[
                         DeclarativeBase,
                         Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int]],
                     ] = None
                     ):
        if options:
            self.options = {}
            self.options.update(options)
        if extra_attrs is not None:
            for attr in extra_attrs.copy():
                if attr in ["disabled", "required", "hidden", "readonly", "value"]:
                    extra_attrs.pop(attr)
            self.extra_attrs.update(extra_attrs)
        if prefix:
            self.prefix = prefix
        if obj:
            self.init_data = self.init_data.copy()
            self.init_data[self.name] = obj.get(f"{self.name}", "")
        self.label_field = self.get_label()
        self.field = self.get_input()
        return self.__html__()

    def update_attrs2(
            self,
            extra_attrs=None,
            obj: Union[
                dict[str, str], dict[int, str], dict[int, int], dict[str, int]
            ] = None,
            prefix=None,
            options: Union[
                DeclarativeBase,
                Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int]],
            ] = None,
    ):
        if options:
            self.options = {}
            self.options.update(options)
        if extra_attrs is not None:
            for attr in extra_attrs.copy():
                if attr in ["disabled", "required", "hidden", "readonly", "value"]:
                    extra_attrs.pop(attr)
            self.extra_attrs.update(extra_attrs)
        if prefix:
            self.prefix = prefix
        if obj:
            self.init_data = self.init_data.copy()
            self.init_data[self.name] = obj.get(f"{self.name}", "")
        return self

    def convert(self, value):
        if not value:
            return None
        try:
            return self.value_type(value)
        except (ValueError, TypeError) as e:  # Ловим только ожидаемые исключения
            raise e

    def default_validator(self, value: Union[str, None]) -> bool:
        self.init_data[self.name] = escape(value)
        setattr(self, "field", self.get_input())
        self.list_error = []
        minlength = int(self.extra_attrs.get("minlength", 0))
        maxlength = int(self.extra_attrs.get("maxlength", 256))
        if value in (None, ""):
            return True
        if value in (None, "") and self.required:
            self.list_error.append(f" Field cannot be empty")
        if not isinstance(value, self.value_type):
            value = self.convert(value)
        if minlength is not None and minlength > len(value):
            self.list_error.append(
                f" The value must be longer than {minlength} and shorter than {maxlength}."
            )
        if maxlength is not None and maxlength < len(value):
            self.list_error.append(
                f" The value must be longer than {minlength} and shorter than {maxlength}."
            )
        if not re.fullmatch(self.pattern, escape(value)):
            special_chars = re.sub(
                r"[a-zA-Zа-яА-Я0-9\s]", "", self.pattern.split("[")[1].split("]")[0]
            )
            special_chars = special_chars.replace("\\", "")
            unique_chars = "".join(
                sorted(set(special_chars), key=lambda x: special_chars.index(x))
            )
            self.list_error.append(
                f" Field value contains invalid characters. Use letters, numbers and {unique_chars}"
            )
        return len(self.list_error) == 0

    def get_options_select(self):
        pass


class TextWidget(BaseWidget):
    type = "text"
    pattern = r"^[a-zA-Zа-яА-Я0-9\s.,\-_!№:?()*]+$"
    value_type = str


class TextAreaWidget(BaseWidget):
    type = "textarea"
    pattern = r"^[a-zA-Zа-яА-Я0-9\s.,\-_!№:?()*]+$"
    value_type = str

    def get_input(self) -> str:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        init_value = escape(str(self.init_data.get(self.name, "")))
        extra_attrs = self.get_extra_attrs()
        return (
            Markup(
                f'<{self.type} name="{value}" id="{value}"'
                f"{attrs}{extra_attrs}>{init_value}</{self.type}>"
            )
            + html_icon
            + Markup("<br>\n")
        )


class EmailWidget(BaseWidget):
    type = "email"
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    value_type = str

    def default_validator(self, value):
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        self.list_error = []
        if not isinstance(value, self.value_type):
            value = self.convert(value)
        if value in (None, "") and self.required:
            self.list_error.append(f" Field cannot be empty")
        if value in (None, "") and not self.required:
            return True
        if not re.fullmatch(self.pattern, escape(value)):
            self.list_error.append(
                " The value does not meet the requirements for an email address."
            )
        return len(self.list_error) == 0


class IntegerWidget(BaseWidget):
    type = "number"
    pattern = r"^-?\d+$"
    value_type = int

    def default_validator(self, value):
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        self.list_error = []
        minlength = self.convert(self.extra_attrs.get("minlength", 0))
        maxlength = self.convert(self.extra_attrs.get("maxlength", 256))
        min = self.convert(self.extra_attrs.get("min", None))
        max = self.convert(self.extra_attrs.get("max", None))
        if (value is None or value == "") and self.required:
            self.list_error.append(f" Field cannot be empty.")
        if (value is None or value == "") and not self.required:
            return True
        if (min is not None and value < min) or (
                max is not None and value > max
        ):
            self.list_error.append(
                f" Field must be greater than {min} and less than {max}"
            )
        if (minlength is not None and len(str(value)) < minlength) or (
                maxlength is not None and len(str(value)) > maxlength
        ):
            self.list_error.append(
                f" The number of characters must be greater than {minlength} and less than {maxlength}"
            )
        if not re.fullmatch(self.pattern, str(value)):
            self.list_error.append(" Value does not meet requirements.")
        return len(self.list_error) == 0


class FloatWidget(BaseWidget):
    type = "number"
    pattern = r"^-?\d+\.\d+$"
    value_type = float

    def default_validator(self, value: Optional[float]) -> bool:
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        self.list_error = []
        min = float(self.extra_attrs.get("min")) if "min" in self.extra_attrs else None
        max = float(self.extra_attrs.get("max")) if "max" in self.extra_attrs else None
        minlength = int(self.extra_attrs.get("minlength", 0))
        maxlength = int(self.extra_attrs.get("maxlength", 256))
        if value in (None, ""):
            if self.required:
                self.list_error.append(f" Field cannot be empty.")
            return not self.required
        if (min is not None and value < min) or (
                max is not None and value > max
        ):
            self.list_error.append(
                f" Length must be between {min} and {max}"
            )
        if len(str(value)) < minlength or len(str(value)) > maxlength:
            self.list_error.append(
                f"Length must be between {minlength} and {maxlength} chars"
            )
        if not re.fullmatch(self.pattern, str(value)):
            self.list_error.append("Invalid format")
        return len(self.list_error) == 0


class RangeWidget(FloatWidget):
    type = "range"
    pattern = r"^-?\d+(\.\d+)?$"
    extra_attrs_type = {
        "step": float,
        "min": float,
        "max": float,
    }

    def get_input(self) -> str:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        init_value = self.get_init_value()
        extra_attrs = self.get_extra_attrs()

        return (
            Markup(
                f'<input type="{self.type}" name="{value}" id="{value}"'
                f"{attrs}{init_value}{extra_attrs} />"
            )
            + html_icon
            + Markup("<br>\n")
        )


class PasswordWidget(BaseWidget):
    type = "password"
    pattern = r"^[a-zA-Zа-яА-Я0-9\s.,_!@#?*№-]+$"
    value_type = str

    def get_input(self) -> Markup:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        extra_attrs = self.get_extra_attrs()

        return (
                Markup(
                    f'<input type="{self.type}" name="{value}" id="{value}"'
                    f"{attrs}{extra_attrs} />"
                )
                + html_icon
                + Markup("<br>\n")
        )

    def get_data_to_dict(self):
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.get_widget_prefix(),
                    "value": "",
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": "",
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict

    def update_attrs(
            self,
            extra_attrs: Union[dict[str, int], dict[str, str]] = None,
            obj: Union[
                dict[str, str], dict[int, str], dict[int, int], dict[str, int]
            ] = None,
            prefix=None,
            options: Union[
                DeclarativeBase,
                Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int]],
            ] = None,
    ):

        return super().update_attrs(extra_attrs, obj, prefix, options)

    def default_validator(self, value: Union[str, None]) -> bool:
        self.list_error = []
        minlength = (
            abs(int(self.extra_attrs.get("minlength", 0)))
            if not self.required
            else abs(int(self.extra_attrs.get("minlength", 4)))
        )
        maxlength = abs(int(self.extra_attrs.get("maxlength", 128)))
        if value in (None, "") and not self.required and minlength == 0:
            return True
        if (value in (None, "") and self.required) or minlength != 0:
            self.list_error.append(f" Value cannot be empty")
        if not isinstance(value, self.value_type):
            value = self.convert(value)
        print(minlength, value, "test")
        if minlength is not None and minlength > len(value) if value is not None else 0:
            self.list_error.append(
                f" Content should be shorter than {minlength} and longer than {maxlength}."
            )
        if maxlength is not None and maxlength < len(value) if value is not None else 0:
            self.list_error.append(
                f" Content should be shorter than {minlength} and longer than {maxlength}."
            )
        if not re.fullmatch(self.pattern, escape(value)):
            special_chars = re.sub(
                r"[a-zA-Zа-яА-Я0-9\s]", "", self.pattern.split("[")[1].split("]")[0]
            )
            special_chars = special_chars.replace("\\", "")
            unique_chars = "".join(
                sorted(set(special_chars), key=lambda x: special_chars.index(x))
            )
            self.list_error.append(
                f" Contains invalid characters. Use letters, numbers and {unique_chars}"
            )
        return len(self.list_error) == 0


class TimeWidget(BaseWidget):
    type = "time"
    pattern = r"^\d{2}:\d{2}:\d{2}$"
    value_type = time

    def convert(self, value: Union[str, time, None]) -> Optional[time]:
        """
        Преобразует строку в формате 'HH:MM:SS' в объект time.
        Если value равно None, возвращает None.
        Если тип value равно time, возвращает value.
        Если преобразование невозможно, выбрасывает ValueError с описанием ошибки.
        """
        if value is None:
            return None
        if isinstance(value, self.value_type):
            return value
        try:
            return self.value_type.fromisoformat(value)
        except ValueError as e:
            raise ValueError(
                f"Invalid time format: {value}. Expected 'HH:MM:SS'."
            ) from e

    def get_init_value(self):
        return "".join(
            f' value="{value.strftime("%H:%M:%S") if isinstance(value, time) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def get_data_to_dict(self):
        current_value = list(self.init_data.values())[0]
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.prefix + "_" + self.name if self.prefix else self.name,
                    "label": self.label_name,
                    "value": (
                        current_value
                        if isinstance(current_value, str)
                        else current_value.strftime("%H:%M:%S")
                    ),
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": (
                    current_value
                    if isinstance(current_value, str)
                    else current_value.strftime("%H:%M:%S")
                ),
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict

    def default_validator(self, value: Optional[time]) -> bool:
        self.list_error = []
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        if value is None:
            if self.required:
                self.list_error.append(f"{self.name} cannot be empty")
            return not self.required
        try:
            min_value = self.convert(self.extra_attrs.get("min", None))
            max_value = self.convert(self.extra_attrs.get("max", None))
            if min_value is not None and value < min_value:
                self.list_error.append(
                    f' Value must be after {min_value.strftime("%Y-%m-%d")}'
                )
            if max_value is not None and value > max_value:
                self.list_error.append(
                    f" Value must be before {max_value.strftime('%Y-%m-%d')}"
                )
        except (TypeError, AttributeError) as e:
            self.list_error.append(f"Invalid range values: {str(e)}")
        return len(self.list_error) == 0


class DateWidget(BaseWidget):
    type = "date"
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    value_type = date

    def convert(self, value: Union[str, date, None]) -> Optional[date]:
        """
        Преобразует строку в формате 'YYYY-MM-DD' в объект date.
        Если value равно None, возвращает None.
        Если тип value равно date, возвращает value.
        Если преобразование невозможно, выбрасывает ValueError с описанием ошибки.
        """
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            raise ValueError(f"Invalid type: {type(value)}. Expected 'str' or 'date'.")
        try:
            return date.fromisoformat(value)
        except ValueError as e:
            raise ValueError(
                f"Invalid date format: {value}. Expected 'YYYY-MM-DD'."
            ) from e

    def get_init_value(self):
        return "".join(
            f' value="{value.strftime("%Y-%m-%d") if isinstance(value, date) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def get_data_to_dict(self):
        current_value = list(self.init_data.values())[0]
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.prefix + "_" + self.name if self.prefix else self.name,
                    "label": self.label_name,
                    "value": (
                        current_value
                        if isinstance(current_value, str)
                        else current_value.strftime("%Y-%m-%d")
                    ),
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": (
                    current_value
                    if isinstance(current_value, str)
                    else current_value.strftime("%Y-%m-%d")
                ),
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict

    def default_validator(self, value: Optional[date]) -> bool:
        self.list_error = []
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        if value is None:
            if self.required:
                self.list_error.append(f" Field cannot be empty")
            return not self.required
        try:
            min_value = self.convert(self.extra_attrs.get("min", None))
            max_value = self.convert(self.extra_attrs.get("max", None))
            if min_value is not None and value < min_value:
                self.list_error.append(
                    f' Value must be after {min_value.strftime("%Y-%m-%d")}'
                )
            if max_value is not None and value > max_value:
                self.list_error.append(
                    f" Value must be before {max_value.strftime('%Y-%m-%d')}"
                )
        except (TypeError, AttributeError) as e:
            self.list_error.append(f"Invalid range values: {str(e)}")
        return len(self.list_error) == 0


class DateTimeWidget(BaseWidget):
    type = "datetime-local"
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
    value_type = datetime

    def convert(self, value: Union[str, datetime, None]) -> Optional[datetime]:
        """
        Преобразует строку в формате 'YYYY-MM-DDTHH:MM:SS' в объект datetime.
        Если value равно None, возвращает None.
        Если тип value равно datetime, возвращает value.
        Если преобразование невозможно, выбрасывает ValueError с описанием ошибки.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError(
                f"Invalid type: {type(value)}. Expected 'str' or 'datetime'."
            )
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid datetime format: {value}. Expected 'YYYY-MM-DDTHH:MM:SS'."
            ) from e

    def get_init_value(self) -> str:
        return "".join(
            f' value="{value.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(value, datetime) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def default_validator(self, value: Optional[datetime]) -> bool:
        self.list_error = []
        self.init_data[self.name] = value
        if value is None:
            if self.required:
                self.list_error.append(f" Field cannot be empty")
            return not self.required
        try:
            min_value = self.convert(self.extra_attrs.get("min", None))
            max_value = self.convert(self.extra_attrs.get("max", None))
            if min_value is not None and value < min_value:
                self.list_error.append(
                    f' Value must be after {min_value.strftime("%Y-%m-%d %H:%M:%S")}'
                )
            if max_value is not None and value > max_value:
                self.list_error.append(
                    f" Value must be before {max_value.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except (TypeError, AttributeError) as e:
            self.list_error.append(f"Invalid range values: {str(e)}")
        setattr(self, "field", self.get_input())
        return len(self.list_error) == 0

    def get_data_to_dict(self):
        current_value = list(self.init_data.values())[0]
        for key, value in self.extra_attrs.items():
            if key in ("min", "max"):
                self.extra_attrs[key] = self.extra_attrs[key].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.get_widget_prefix(),
                    "value": (
                        current_value
                        if isinstance(current_value, str)
                        else current_value.strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": (
                    current_value
                    if isinstance(current_value, str)
                    else current_value.strftime("%T-%m-%d %H:%M:%S")
                ),
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict


class SelectWidget(BaseWidget):
    type = "select"
    value_type = str

    def get_input(self) -> str:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        options_select = self.get_options_select()
        extra_attrs = self.get_extra_attrs()

        return (
            Markup(
                f'<{self.type} name="{value}" id="{value}"'
                f"{attrs}{extra_attrs}>{options_select}</{self.type}>"
            )
            + html_icon
            + Markup("<br>\n")
        )

    def get_options_select(self) -> str:
        # Генерация HTML для каждого ключа и списка значений
        if self.options:
            options_select = f'\n<optgroup label="{self.label_name}">\n'
            options_select += '<option value="" hidden>---select---</option>\n'
            for pk, value in self.options.items():
                try:
                    if pk in list(self.get_init_value().values()):
                        options_select += "".join(
                            f'<option value="{pk}" selected>{value}</option>\n'
                        )
                    else:
                        options_select += "".join(
                            f'<option value="{pk}">{value}</option>\n'
                        )
                except Exception:
                    options_select += "".join(
                        f'<option value="{pk}">{value}</option>\n'
                    )

            options_select += "</optgroup>\n"
            return options_select
        return ""

    def get_widget_attrs(self) -> str:
        attrs = (
                (' class="readonly"' if self.readonly else "")
                + (" required" if self.required else "")
                + (" disabled" if self.disabled else "")
        )
        return attrs

    def get_init_value(self) -> dict[str, str] | None:
        """
        Метод, возвращающий строковое представление с начальными значениями для полей.
        :return: dict
        """
        for key, value in self.init_data.items():
            try:
                return {key: str(value.name)}
            except Exception:
                return {key: str(value)}

    def get_data_to_dict(self):
        current_value: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    current_value = value.name
                except:
                    current_value = value
        else:
            current_value = ""
        if not self.list_error:
            widget_dict = {
                self.name: {
                    "type": self.type,
                    "name": self.get_widget_prefix(),
                    "value": current_value,
                    "attrs": {},
                }
            }
            if self.extra_attrs:
                widget_dict[self.name]["attrs"].update(self.extra_attrs)
            if self.hidden:
                widget_dict[self.name]["attrs"]["hidden"] = True
            if self.readonly:
                widget_dict[self.name]["attrs"]["readonly"] = True
            if self.required:
                widget_dict[self.name]["attrs"]["required"] = True
            if self.disabled:
                widget_dict[self.name]["attrs"]["disabled"] = True
            if self.extensions:
                widget_dict[self.name]["attrs"]["extensions"] = self.extensions
            if self.options:
                widget_dict[self.name]["options"] = self.options
            return True, widget_dict
        widget_dict = {
            self.name: {
                "type": "error",
                "value": list(self.init_data.values())[0],
                "detail": "".join(value for value in self.list_error),
            }
        }
        return False, widget_dict

    def default_validator(self, value):
        self.list_error = []
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        if value in (None, ""):
            if self.required:
                self.list_error.append(f" Field cannot be empty")
        if value in list(self.options.keys()):
            return True
        self.list_error.append(f" Invalid value for {self.name}")
        return len(self.list_error) == 0


class CheckboxWidget(BaseWidget):
    type = "checkbox"
    value_type = bool

    def get_init_value(self) -> str:
        return " checked" if self.init_data.get(self.name) is True else ""

    def convert(self, value) -> Optional[bool]:
        if value in (None, ""):
            return False
        if str(value).lower() in ["true", "1", "on", "yes"]:
            return True
        if value in [True, 1]:
            return True
        return False

    def default_validator(self, value):
        self.list_error = []
        self.init_data[self.name] = value
        setattr(self, "field", self.get_input())
        if value in (None, "", False) and self.required:
            self.list_error.append(f" {self.name} cannot be empty.")
        return len(self.list_error) == 0


class FileWidget(BaseWidget):
    type = "file"
    pattern = r"^.+(\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.txt)$"
    value_type = str

    def get_input(self) -> str:
        html_icon = Markup(" <em>*</em>") if self.required else Markup("")
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        extra_attrs = self.get_extra_attrs()
        save_file = (
            self.init_data.get(self.name)
            if isinstance(self.init_data.get(self.name), str)
            else ""
        )
        detail = (
            Markup(f'<small class="file" id="{value}">saved file: {save_file}</small>')
            if save_file
            else Markup("")
        )  # if self.init_data.get(self.name, None) else ""

        return (
                Markup(
                    f'<input type="{self.type}" name="{value}" id="{value}"'
                    f"{attrs}{extra_attrs} />"
                )
                + html_icon
                + detail
                + Markup("<br>\n")
        )

    def get_widget_attrs(self) -> str:
        if self.extensions:
            accept_ext = ", ".join(self.extensions)
        else:
            default_extensions = re.findall(r"\\\.(\w+)", self.pattern)
            accept_ext = ", ".join(f".{ext}" for ext in default_extensions)

        attrs = (
                (" required" if self.required else "")
                + (" disabled" if self.disabled else "")
                + f' accept="{accept_ext}"'
        )
        return attrs

    def get_extensions_pattern(self):
        # в словарь добавлен самый минимум
        extension_groups = {
            "image/*": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "document/*": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"],
            "audio/*": [".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a", ".wma"],
            "video/*": [
                ".mp4",
                ".avi",
                ".mkv",
                ".mov",
                ".wmv",
                ".flv",
                ".webm",
                ".mpeg",
            ],
            "archive/*": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
            "text/*": [".txt", ".csv", ".json", ".xml", ".html", ".css", ".js", ".log"],
        }
        if self.extensions and isinstance(self.extensions, list):
            expanded_extensions = []
            for ext in self.extensions:
                if ext in extension_groups:
                    expanded_extensions.extend(extension_groups[ext])
                else:
                    expanded_extensions.append(ext)
            extensions_pattern = "|".join(
                re.escape(ext) for ext in expanded_extensions if isinstance(ext, str)
            )
            return rf"^.+(?:{extensions_pattern})$"
        return self.pattern

    def default_validator(self, value):
        self.list_error = []
        if value in (None, "") and not self.required:
            return True
        if hasattr(value, "size") and value.size == 0 and self.required:
            self.list_error.append(f" {self.name} cannot be empty.")
        if not hasattr(value, "filename"):
            self.list_error.append(f" {self.name} is invalid: data type is unknown.")
        if value.size == 0 and not self.required:
            return True
        extensions = self.get_extensions_pattern()
        if value.filename != "":
            try:
                if re.fullmatch(extensions, value.filename):
                    return True
            except re.error:
                self.list_error.append(
                    f" The selected file: {value.filename} type is not supported."
                )
        if self.list_error:
            setattr(self, "field", self.get_input())
        return len(self.list_error) == 0

    def convert(self, value):
        if not value.size:
            return None
        return value


class ImageWidget(FileWidget):
    pattern = r"^.+(\.jpg|\.jpeg|\.png|\.gif|\.bmp|\.webp)$"

    def get_widget_attrs(self) -> str:
        accept_ext = ", ".join(self.extensions)
        attrs = (
            (" required" if self.required else "")
            + (" disabled" if self.disabled else "")
            + f' accept="{accept_ext}"'
        )
        return attrs

    @property
    def show(self):
        file_path = escape(self.init_data.get(self.name))
        return Markup(f'<img src="{file_path}" alt="Image"')
