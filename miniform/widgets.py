import re
from abc import abstractmethod, ABC
from datetime import datetime, date, time
from functools import wraps
from typing import Union, Dict, Any, Optional
import nest_asyncio

from sqlalchemy.orm import DeclarativeBase


class AbstractWidget(ABC):
    pattern = None

    def __init__(
            self,
            name: str = None,
            label: str = None,
            readonly: bool = False,
            hidden: bool = False,
            required: bool = False,
            disabled: bool = False,
            extra_attrs: Union[dict[str, Union[str, int]]] = None,
            init_data: Union[dict[str, Union[str, int]], dict[int, Union[str, int]]] = None,
            options: Union[dict[str, Union[str, int]], dict[int, Union[str, int]]] = None,
            extensions: str = None,
            prefix: str = None,
            error: str = None,
            validator=None
    ):
        self.name = name or None
        self.label_name = label
        self.hidden = hidden or False
        self.readonly = readonly or False
        self.required = required or False
        self.disabled = disabled or False
        self.extra_attrs = extra_attrs or {}
        self.init_data = init_data or {}
        self.options = options or {}
        self.extensions = extensions or None
        self.prefix = prefix or None
        self.error = error or ""
        self.to_dict: Dict[str, Any] = {}
        self.default_validator = validator or self.default_validator

    def __set_name__(self, owner, name):
        self.name = name

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
    def update_attrs(
            self,
            extra_attrs: Union[dict[str, str], dict[str, int]] = None,
            obj=None,
            prefix: str = None,
            options: Union[
                DeclarativeBase,
                Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int]],
            ] = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def convert(self, value):
        raise NotImplementedError

    def get_options_select(self):
        pass

    def get_init_value(self):
        pass

    def get_data_to_dict(self):
        pass

    def get_widget_prefix(self):
        pass

    def get_extra_attrs(self):
        pass

    def get_widget_attrs(self):
        pass


class BaseWidget(AbstractWidget):
    type = None

    @wraps(AbstractWidget.__init__)
    def __init__(self, *args, **kwargs):
        nest_asyncio.apply()
        super().__init__(*args, **kwargs)
        self.label_field = self.get_label()
        self.field = self.get_input()

    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        raise ValueError(f"The object {self.__class__.__name__} is not {item} in the dictionary")

    def __str__(self):
        field_hidden = " hidden" if self.hidden is True else ""
        error = f' <small class="error" id="{self.type}">error: {self.error}</small>' if self.error else ""
        return (
                f'<div class="form-group"{field_hidden}>\n'
                + self.label_field
                + self.field
                + error
                + "</div>\n"
        )

    def __html__(self):
        field_hidden = " hidden" if self.hidden is True else ""
        error = f' <small class="error" id="{self.type}">error: {self.error}</small>' if self.error else ""
        return (
                f'<div class="form-group"{field_hidden}>\n'
                + self.label_field
                + self.field
                + error
                + "</div>\n"
        )

    def get_data_to_dict(self) -> Dict[str, Any]:
        current_value: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    current_value = value.name
                except:
                    current_value = value
        else:
            current_value = ""
        widget_dict = {self.name: {
            "type": self.type,
            "name": self.prefix + "_" + self.name if self.prefix else self.name,
            "label": self.label_name,
            "value": current_value,
            "attrs": {},
        }}
        if self.error:
            widget_dict[self.name]["error"] = self.error
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
        return widget_dict

    def get_widget_prefix(self):
        if self.prefix:
            return self.prefix + "_" + self.name
        return self.name

    def get_init_value(self):
        return "".join(
            f' value="{value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def get_widget_attrs(self) -> str:
        attrs = (
                (" readonly" if self.readonly else "")
                + (" required" if self.required else "")
                + (" disabled" if self.disabled else "")
        )
        return attrs

    def get_label(self) -> str:
        value = self.get_widget_prefix()
        return f'<label for="{value}">{self.label_name}</label>\n'

    def get_extra_attrs(self) -> str:
        """
        Метод возвращающий строковое представление дополнительных атрибутов поля.
        :return: str
        """
        return "".join(
            f' {key}="{value}"'
            for key, value in self.extra_attrs.items()
            if self.extra_attrs != {}
            if value != ""
        )

    def get_input(self) -> str:
        html_icon = " <em>*</em>" if self.required else ""
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        init_value = self.get_init_value()
        extra_attrs = self.get_extra_attrs()
        return (
                f'<input type="{self.type}" name="{value}" id="{value}"{attrs}{init_value}{extra_attrs} />'
                + html_icon
                + "<br>\n"
        )

    def update_attrs(
            self,
            extra_attrs: Union[dict[str, str], dict[str, int]] = None,
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
        setattr(self, "label_field", self.get_label())
        setattr(self, "field", self.get_input())
        return self

    def convert(self, value):
        if value == "":
            return None
        if hasattr(self, "_convert"):
            return self._convert(value)
        return value

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        min_length = self.extra_attrs.get("min", 0)
        max_length = self.extra_attrs.get("max", 128)
        if (min_length is not None and min_length > len(value)) or (max_length is not None and max_length < len(value)):
            self.error += f" Content must be shorter than {max_length} characters and longer than {min_length} character."
            return self.error
        if re.fullmatch(self.pattern, value):
            return True
        special_chars = ".,-_!№:?()*"
        unique_chars = ''.join(sorted(set(special_chars), key=lambda x: special_chars.index(x)))
        self.error += f" Contains invalid characters. Use letters, numbers and {unique_chars}"
        return self.error

    def get_options_select(self):
        return None


class TextWidget(BaseWidget):
    type = "text"
    pattern = r'^[a-zA-Zа-яА-Я0-9\s.,\-_!№:?()*]+$'


class TextAreaWidget(BaseWidget):
    type = "textarea"
    pattern = r'^[a-zA-Zа-яА-Я0-9\s.,\-_!№:?()*]+$'

    def get_input(self) -> str:
        html_icon = " <em>*</em>" if self.required else ""
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        init_value = self.init_data[self.name] if self.init_data else ""
        extra_attrs = self.get_extra_attrs()
        return (
                f'<{self.type} name="{value}" id="{value}"{attrs}{extra_attrs}>{init_value}</{self.type}>'
                + html_icon
                + "<br>\n"
        )


class EmailWidget(BaseWidget):
    type = "email"
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty"
            return self.error
        if isinstance(value, str):
            try:
                if re.fullmatch(self.pattern, value):
                    return True
            except re.error:
                self.error += " The value does not meet the requirements for an email address."
                return self.error
        else:
            self.error += f" {self.name} must be a string."
            return self.error


class IntegerWidget(BaseWidget):
    type = "number"
    pattern = r'^-?\d+$'

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        try:
            value_int = int(value)
        except (ValueError, TypeError):
            self.error += f" {self.name} must be a integer."
            return self.error
        min_value = self.extra_attrs.get("min", None)
        max_value = self.extra_attrs.get("max", None)
        if min_value is not None:
            try:
                min_value = int(min_value)
            except (ValueError, TypeError) as e:
                raise e
        if max_value is not None:
            try:
                max_value = int(max_value)
            except (ValueError, TypeError) as e:
                raise e
        if (min_value is not None and value_int < min_value) or (max_value is not None and value_int > max_value):
            if min_value is not None and max_value is not None:
                self.error += f" The value must be between {min_value} and {max_value}."
            elif min_value is not None:
                self.error += f" The value must be greater than or equal to {min_value}."
            elif max_value is not None:
                self.error += f" The value must be less than or equal to {max_value}."
            return self.error
        if isinstance(value, str) and re.fullmatch(self.pattern, value):
            return True
        self.error += " Value does not meet requirements."
        return self.error


class FloatWidget(BaseWidget):
    type = "number"
    pattern = r'^-?\d+\.\d+$'

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        try:
            value_int = float(value)
        except (ValueError, TypeError):
            self.error += f" {self.name} must be a float."
            return self.error
        min_value = self.extra_attrs.get("min", None)
        max_value = self.extra_attrs.get("max", None)
        if min_value is not None:
            try:
                min_value = float(min_value)
            except (ValueError, TypeError) as e:
                raise e
        if max_value is not None:
            try:
                max_value = float(max_value)
            except (ValueError, TypeError) as e:
                raise e
        if (min_value is not None and value_int < min_value) or (max_value is not None and value_int > max_value):
            if min_value is not None and max_value is not None:
                self.error += f" The value must be between {min_value} and {max_value}."
            elif min_value is not None:
                self.error += f" The value must be greater than or equal to {min_value}."
            elif max_value is not None:
                self.error += f" The value must be less than or equal to {max_value}."
            return self.error
        if isinstance(value, str) and re.fullmatch(self.pattern, value):
            return True
        self.error += " Value does not meet requirements."
        return self.error


class RangeWidget(BaseWidget):
    type = "range"
    pattern = r'^-?\d+(\.\d+)?$'

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error = f" {self.name} cannot be empty."
            return self.error
        if not re.fullmatch(self.pattern, value):
            self.error = f" {self.name} must be a valid float."
            return self.error
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            self.error = f" {self.name} must be a valid float."
            return self.error
        min_value = self.extra_attrs.get("min", None)
        max_value = self.extra_attrs.get("max", None)
        if min_value is not None:
            try:
                min_value = float(min_value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid 'min' value in extra_attrs for {self.name}.")
        if max_value is not None:
            try:
                max_value = float(max_value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid 'max' value in extra_attrs for {self.name}.")
        if min_value is not None and value_float < min_value:
            self.error = f" The value must be greater than or equal to {min_value}."
            return self.error
        if max_value is not None and value_float > max_value:
            self.error = f" The value must be less than or equal to {max_value}."
            return self.error
        return True


class PasswordWidget(BaseWidget):
    type = "password"
    pattern = r'^[a-zA-Zа-яА-Я0-9\s.,\-_!@#?*№]+$'

    def get_input(self) -> str:
        html_icon = " <em>*</em>" if self.required else ""
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        extra_attrs = self.get_extra_attrs()
        return (
                f'<input type="{self.type}" name="{value}" id="{value}"{attrs}{extra_attrs} />'
                + html_icon
                + "<br>\n"
        )

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty"
            return self.error
        if not re.fullmatch(self.pattern, value):
            self.error += f" Password does not meet requirements. Use letters, numbers and symbols .,-_!@#?*№"
        min_length = self.extra_attrs.get("min", 3)
        max_length = self.extra_attrs.get("max", 128)
        if (min_length is not None and min_length > len(value)) or (max_length is not None and max_length < len(value)):
            self.error += f" The password length must be between {min_length} and {max_length} characters."
        if self.error:
            return self.error
        return True


class TimeWidget(BaseWidget):
    type = "time"
    pattern = r'^\d{2}:\d{2}:\d{2}$'

    def _convert(self, value: Union[str, time, None]) -> Optional[time]:
        """
        Преобразует строку в формате 'HH:MM:SS' в объект time.
        Если value равно None, возвращает None.
        Если тип value равно time, возвращает value.
        Если преобразование невозможно, выбрасывает ValueError с описанием ошибки.
        """
        if value is None:
            return None
        if isinstance(value, time):
            return value
        try:
            return time.fromisoformat(value)
        except ValueError as e:
            raise ValueError(f"Invalid time format: {value}. Expected 'HH:MM:SS'.") from e

    def get_init_value(self):
        return "".join(
            f' value="{value.strftime("%H:%M:%S") if isinstance(value, time) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def get_data_to_dict(self) -> Dict[str, Any]:
        selected_name: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    selected_name = value.name
                except:
                    selected_name = value
        else:
            selected_name = ""
        widget_dict = {self.name: {
            "type": self.type,
            "name": self.prefix + "_" + self.name if self.prefix else self.name,
            "label": self.label_name,
            "value": selected_name if isinstance(selected_name, str) else selected_name.strftime("%H:%M:%S"),
            "attrs": {},
        }}
        if self.error:
            widget_dict[self.name]["error"] = self.error
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
        return widget_dict

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required is None:
            return True
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        try:
            current_value = self._convert(value)
        except ValueError as e:
            self.error += f" {str(e)}"
            return self.error
        try:
            min_length = self._convert(self.extra_attrs.get("min", None))
            max_length = self._convert(self.extra_attrs.get("max", None))
        except ValueError as e:
            raise e
        if (min_length is not None and min_length > current_value) or (
                max_length is not None and max_length < current_value):
            self.error += f" {self.name} is out of range."
            return self.error
        if isinstance(value, str):
            try:
                if re.fullmatch(self.pattern, value):
                    return True
            except re.error:
                self.error += f" Invalid time format: {value}. Expected 'HH:MM:SS'."
                return self.error
        elif isinstance(value, time):
            return True
        else:
            self.error += f" {self.name} must be a string."
            return self.error
        self.error += " Time format does not match the required one."
        return self.error


class DateWidget(BaseWidget):
    type = "date"
    pattern = r'^\d{4}-\d{2}-\d{2}$'

    def _convert(self, value: Union[str, date, None]) -> Optional[date]:
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
            raise ValueError(f"Invalid date format: {value}. Expected 'YYYY-MM-DD'.") from e

    def get_init_value(self):
        return "".join(
            f' value="{value.strftime("%Y-%m-%d") if isinstance(value, date) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def get_data_to_dict(self) -> Dict[str, Any]:
        selected_name: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    selected_name = value.name
                except:
                    selected_name = value
        else:
            selected_name = ""
        widget_dict = {self.name: {
            "type": self.type,
            "name": self.prefix + "_" + self.name if self.prefix else self.name,
            "label": self.label_name,
            "value": selected_name if isinstance(selected_name, str) else selected_name.strftime("%Y-%m-%d"),
            "attrs": {}
        }}
        if self.error:
            widget_dict[self.name]["error"] = self.error
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
        return widget_dict

    def default_validator(self, value: Union[str, date, None]):
        self.error = ""
        if (value is None or value == "") and self.required is None:
            return True
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        try:
            current_value = self._convert(value)
        except ValueError as e:
            self.error += f" {str(e)}"
            return self.error
        try:
            min_date = self._convert(self.extra_attrs.get("min", None))
            max_date = self._convert(self.extra_attrs.get("max", None))
        except ValueError as e:
            raise e
        if (min_date is not None and min_date > current_value) or (max_date is not None and max_date < current_value):
            self.error += f" {self.name} is out of range."
            return self.error
        if isinstance(value, str):
            try:
                if re.fullmatch(self.pattern, value):
                    return True
            except re.error:
                self.error += f" Invalid date format: {value}. Expected 'YYYY-MM-DD'."
                return self.error
        elif isinstance(value, date):
            return True  # Если value уже является объектом date, считаем его валидным
        else:
            self.error += f" {self.name} must be a string or date object."
            return self.error
        self.error += " Date format does not match the required one."
        return self.error


class DateTimeWidget(BaseWidget):
    type = "datetime-local"
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'

    def _convert(self, value: Union[str, datetime, None]) -> Optional[datetime]:
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
            raise ValueError(f"Invalid type: {type(value)}. Expected 'str' or 'datetime'.")
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {value}. Expected 'YYYY-MM-DDTHH:MM:SS'.") from e

    def get_init_value(self) -> str:
        return "".join(
            f' value="{value.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(value, datetime) else value}"'
            for key, value in self.init_data.items()
            if self.init_data != {}
            and key == self.name
            and value != ""
            and value != "None"
        )

    def default_validator(self, value: Union[str, datetime, None]):
        self.error = ""
        if value is None and self.required is None:
            return True
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        try:
            current_value = self._convert(value)
        except ValueError as e:
            self.error += f" {str(e)}"
            return self.error
        try:
            min_datetime = self._convert(self.extra_attrs.get("min", None))
            max_datetime = self._convert(self.extra_attrs.get("max", None))
        except ValueError as e:
            raise e
        if (min_datetime is not None and min_datetime > current_value) or (
                max_datetime is not None and max_datetime < current_value):
            self.error += f" {self.name} is out of range."
            return self.error
        if isinstance(value, str):
            try:
                if re.fullmatch(self.pattern, value):
                    return True
            except re.error:
                self.error += f" Invalid datetime format: {value}. Expected 'YYYY-MM-DDTHH:MM:SS'."
                return self.error
        elif isinstance(value, datetime):
            return True  # Если value уже является объектом datetime, считаем его валидным
        else:
            self.error += f" {self.name} must be a string or datetime object."
            return self.error
        self.error += " Datetime format does not match the required one."
        return self.error

    def get_data_to_dict(self) -> Dict[str, Any]:
        selected_name: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    selected_name = value.name
                except:
                    selected_name = value
        else:
            selected_name = ""
        widget_dict = {self.name: {
            "type": self.type,
            "name": self.prefix + "_" + self.name if self.prefix else self.name,
            "label": self.label_name,
            "value": selected_name if isinstance(selected_name, str) else selected_name.strftime("%Y-%m-%dT%H:%M:%S"),
            "attrs": {}
        }}
        if self.error:
            widget_dict[self.name]["error"] = self.error
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
        return widget_dict


class SelectWidget(BaseWidget):
    type = "select"

    def get_input(self) -> str:
        html_icon = " <em>*</em>" if self.required else ""
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        options_select = self.get_options_select()
        extra_attrs = self.get_extra_attrs()
        return (
                f'<{self.type} name="{value}" id="{value}"{attrs}{extra_attrs}>{options_select}</{self.type}>'
                + html_icon
                + "<br>\n"
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

    def get_init_value(self) -> dict:
        """
        Метод, возвращающий строковое представление с начальными значениями для полей.
        :return: dict
        """
        for key, value in self.init_data.items():
            try:
                return {key: str(value.name)}
            except Exception:
                return {key: str(value)}

    def default_validator(self, value):
        self.error = ""
        if (value is None or value == "") and self.required:
            self.error += f" {self.name} cannot be empty"
            return self.error
        if value in list(self.options.keys()):
            return True
        self.error += f" Invalid value for {self.name}"
        return self.error

    def get_data_to_dict(self) -> Dict[str, Any]:
        current_value: Union[str, int, Any] = None
        if self.init_data:
            for key, value in self.init_data.items():
                try:
                    current_value = value.name
                except:
                    current_value = value
        else:
            current_value = ""
        widget_dict = {self.name: {
            "type": self.type,
            "name": self.prefix + "_" + self.name if self.prefix else self.name,
            "label": self.label_name,
            "value": current_value,
            "attrs": {},
        }}
        if self.error:
            widget_dict[self.name]["error"] = self.error
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
        return widget_dict


class CheckboxWidget(BaseWidget):
    type = "checkbox"

    def get_init_value(self) -> str:
        return " checked" if self.init_data.get(self.name) is True else ""

    def _convert(self, value):
        if value is None or value == "":
            return False
        if str(value).lower() in ["true", "1", "on", "yes"]:
            return True
        if value in [True, 1]:
            return True
        return False

    def default_validator(self, value):
        self.error = ""
        if self._convert(value) or (self._convert(value) and self.required):
            return True
        self.error += " Invalid value for checkbox field"
        return self.error


class FileWidget(BaseWidget):
    type = "file"
    pattern = r'^.+(\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.txt)$'

    def get_input(self) -> str:
        html_icon = " <em>*</em>" if self.required else ""
        attrs = self.get_widget_attrs()
        value = self.get_widget_prefix()
        extra_attrs = self.get_extra_attrs()
        save_file = self.init_data.get(self.name) if isinstance(self.init_data.get(self.name), str) else ""
        detail = f'<small class="file" id="{value}">saved file: {save_file}</small>' if save_file else ""  # if self.init_data.get(self.name, None) else ""
        return (
                f'<input type="{self.type}" name="{value}" id="{value}"{attrs}{extra_attrs} />'
                + html_icon
                + detail
                + "<br>\n"
        )

    def get_widget_attrs(self) -> str:
        if self.extensions:
            accept_ext = ", ".join(self.extensions)
        else:
            default_extensions = re.findall(r'\\\.(\w+)', self.pattern)
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
            "video/*": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg"],
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
            extensions_pattern = "|".join(re.escape(ext) for ext in expanded_extensions if isinstance(ext, str))
            return rf'^.+(?:{extensions_pattern})$'
        return self.pattern

    def default_validator(self, value):
        self.error = ""
        if hasattr(value, "size") and value.size == 0 and self.required:
            self.error += f" {self.name} cannot be empty."
            return self.error
        if not hasattr(value, "filename"):
            self.error += f" {self.name} is invalid: data type is unknown."
            return self.error
        if value.filename == "" and not self.required:
            return True
        extensions = self.get_extensions_pattern()
        if value.filename != "":
            try:
                if re.fullmatch(extensions, value.filename):
                    return True
            except re.error:
                self.error += " The selected file type is not supported."
                return self.error
        # return self.error


class ImageWidget(FileWidget):
    pattern = r'^.+(\.jpg|\.jpeg|\.png|\.gif|\.bmp|\.webp)$'

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
        return f'<img src="{self.init_data.get(self.name)}" alt="Image"'
