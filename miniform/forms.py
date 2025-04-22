import asyncio
import copy
import datetime
import enum

import nest_asyncio
from typing import (
    Sequence,
    Union,
    Type,
    List,
    Dict,
    Optional,
    Any,
    Callable,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper, DeclarativeBase
from sqlalchemy import (
    select,
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    Float,
    Numeric,
    Time,
    Text,
    Enum,
)
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept
from starlette.datastructures import UploadFile, FormData

from miniform.fields import *
from miniform.widgets import *
from miniform.utils import get_class_name_with_table_name


class BaseForm:
    disabled = []
    exclude = []
    protect = []
    hidden = []
    readonly = []

    def __init__(self):
        self.errors = None
        self._fields: Dict[str, Any] = {}
        self._session: Optional[AsyncSession] = None
        self._obj: Optional[Union[DeclarativeBase, dict]] = None

    def __str__(self) -> str:
        """

        Returns:
            str

        """
        return f"{self.__class__.__name__}"

    def __html__(self) -> str:
        """
        Метод возвращает строку с html кодом формы.

        Returns:
            str
        """
        form_fieldset = (
                "<fieldset>\n"
                + (
                    "".join(
                        f"{widget}"
                        for field, widget in self.fields.items()
                        if field not in self.exclude
                    )
                )
                + "</fieldset>\n"
        )
        return form_fieldset

    def form_dict(self) -> dict:
        """
        Метод приведения полей в формат словаря.
        Returns:
            dict
        """
        data = {}
        data_error = {}
        for field, widget in self.fields.items():
            if field not in self.exclude:
                result, data_to_dict = widget.get_data_to_dict()
                if result:
                    data.update(data_to_dict)
                else:
                    data_error.update(data_to_dict)
        if data_error:
            return data_error
        return data

    def form_json(self, indent=None, ensure_ascii=None):
        """
        Метод приведения словаря полей формы в формат json.
        Args:
            indent: int
            ensure_ascii: bool

        Returns:
            json
        """
        return json.dumps(
            self.form_dict(),
            indent=indent if indent else 2,
            ensure_ascii=ensure_ascii if ensure_ascii else False,
        )

    def __getitem__(self, item) -> AbstractWidget:
        """
        Args:
            item:
                str
        Returns:
            Type[AbstractWidget]
        """
        if item in self._fields:
            return self._fields[item]
        raise AttributeError(f'"{item}" is not a attribute in class {self.__class__}')

    def __getattr__(self, item) -> AbstractWidget:
        """
        Args:
            item:
                str
        Returns:
            Type[AbstractWidget]
        """
        if item in self._fields:
            return self._fields[item]
        raise AttributeError(f'"{item}" is not a attribute in class {self.__class__}')

    @property
    def session(self) -> Optional[AsyncSession]:
        return self._session

    @session.setter
    def session(self, value: AsyncSession) -> None:
        self._session = value

    @property
    def fields(self) -> Dict[str, Any]:
        return self._fields

    @fields.setter
    def fields(self, value: Dict[str, Any]) -> None:
        self._fields.update(value)

    @property
    def obj(self):
        return self._obj

    async def _convert_value_to_required_format(self, data: dict) -> dict:
        """
        Конвертирует значения словаря в требуемый формат.

        Args:
            data: dict
        Returns:
            dict
        """
        converted_data = {}
        for field, value in data.items():
            try:
                converted_data[field] = self.fields[field].convert(value)
            except (ValueError, TypeError):
                converted_data[field] = value
        return converted_data

    @staticmethod
    async def _convert_form_data_to_dict(form_data: Union[dict, FormData, DeclarativeBase]) -> dict:
        """
        Получает данные формы и возвращает в формате словаря.

        Args:
            form_data:
                Union[dict, FormData, DeclarativeBase] - данные формы.
        Returns:
            dict - словарь с данными
        """
        if isinstance(form_data, dict):
            return form_data
        if isinstance(form_data, FormData):
            return dict(form_data.multi_items())
        return form_data.__dict__

    async def _cleaned_form(self, form_data) -> Dict:
        """
        Конвертирует входящие данные в словарь, удаляет пары ключ-значение не соответствующие полям формы.

        Args:
            form_data: dict

        Returns:
            dict
        """
        dict_form = await self._convert_form_data_to_dict(form_data)
        for key, value in dict_form.copy().items():
            if key not in self.fields.keys():
                dict_form.pop(key)
        dict_form = await self._convert_value_to_required_format(dict_form)
        dict_form = await self._add_checkbox_value(dict_form)
        return dict_form


class ModelForm(BaseForm):
    model: Type[DeclarativeBase] = None

    def __init__(
            self,
            session: Optional[AsyncSession] = None,
            obj: Optional[Union[DeclarativeBase, dict]] = None,
            prefix_form=None,
            extend_disabled: List[str] = None,
            extend_exclude: List[str] = None,
            extend_protect: List[str] = None,
            extend_hidden: List[str] = None,
            extend_readonly: List[str] = None,
            replace_disabled: List[str] = None,
            replace_exclude: List[str] = None,
            replace_protect: List[str] = None,
            replace_hidden: List[str] = None,
            replace_readonly: List[str] = None,
    ):
        super().__init__()
        nest_asyncio.apply()
        self.session = session
        self._obj = (
            obj if isinstance(obj, dict) else obj.__dict__ if obj is not None else None
        )
        self.prefix_form = prefix_form
        self.disabled = list(self.disabled)
        self.exclude = list(self.exclude)
        self.protect = list(self.protect)
        self.hidden = list(self.hidden)
        self.readonly = list(self.readonly)
        self.errors = {}
        params_mapping = [
            ("disabled", replace_disabled, extend_disabled),
            ("exclude", replace_exclude, extend_exclude),
            ("protect", replace_protect, extend_protect),
            ("hidden", replace_hidden, extend_hidden),
            ("readonly", replace_readonly, extend_readonly),
        ]
        for attr, replace, extend in params_mapping:
            if replace is not None:
                getattr(self, attr).clear()
                getattr(self, attr).extend(replace)
            elif extend is not None:
                getattr(self, attr).extend(extend)
        asyncio.run(self._get_form_fields())

    async def _check_unique_value(self, field: str, value: Any):
        """
            Проверяет, является ли значение уникальным для указанного поля модели.

            Args:
                field: Имя поля для проверки уникальности
                value: Значение для проверки

            Returns:
                bool: True если значение уникально или поле не уникальное, False если значение уже существует

            Raises:
                AttributeError: Если отсутствует подключение к БД
                SQLAlchemyError: При ошибках работы с базой данных
            """
        if not self._session:
            raise AttributeError(f'No database session in class {self.__class__.__name__}')
        mapper = class_mapper(self.model)
        if field not in mapper.columns:
            raise AttributeError(f"Field '{field}' does not exist in model {self.model.__name__}")
        if not mapper.columns[field].unique:
            return True
        try:
            result = await self._session.execute(
                select(self.model).where(mapper.columns[field] == value))
            obj = result.scalar_one_or_none()
            return obj is None
        except Exception as e:
            await self._session.rollback()
            raise e
        finally:
            await self._session.aclose()

    async def _add_checkbox_value(self, formated_data):
        """
        Добавляет в словарь значение False для полей типа checkbox при их отсутствии.

        Args:
            formated_data: dict

        Returns:
            dict
        """
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            if isinstance(column.type, Boolean):
                if column.name not in formated_data:
                    formated_data[column.name] = False
        return formated_data

    async def is_valid(self, form_data) -> bool:
        """
        Валидирует данные формы и заполняет self._obj корректными значениями.

        Args:
            form_data: Данные формы (обычно dict или FormData)

        Returns:
            bool: True если все данные валидны, False если есть ошибки

        Side Effects:
            - Заполняет self._obj валидными значениями
            - Заполняет self.errors сообщениями об ошибках
        """
        self._obj = {}
        self.errors = {}
        cleaned_data = await self._cleaned_form(form_data)
        for field_name, field_value in cleaned_data.items():
            if field_name not in self.fields:
                continue
            is_valid = self.fields[field_name].default_validator(field_value)
            if not is_valid:
                self.errors[field_name] = ', '.join(map(str, self.fields[field_name].list_error))
                continue
            if self.model:
                try:
                    if not await self._check_unique_value(field_name, field_value):
                        self.fields[field_name].list_error.append("Value must be unique")
                        self.errors[field_name] = ', '.join(map(str, self.fields[field_name].list_error))
                        continue
                except Exception as e:
                    self.fields[field_name].list_error.append(f"Unique check failed: {str(e)}")
                    self.errors[field_name] = ', '.join(map(str, self.fields[field_name].list_error))
                    continue
            self._obj[field_name] = field_value
        return len(self.errors) == 0

    async def save_form(
            self,
    ) -> DeclarativeBase:
        """
        Метод сохранения данных формы.

        Returns:
            DeclarativeBase - объект из базы данных.
        """
        if self._session is None:
            raise ValueError(
                f"Saving a model {self.model} object from a form is impossible without a session."
            )
        for key in self.obj.keys():
            if (
                    key == self.model.__table__.primary_key.columns.keys()[0]
                    and self.obj.get(key) != ""
            ):
                return await self._update_object_form(self.obj)
        return await self._save_object_form(self.obj)

    async def _save_object_form(self, data):
        """
        Создает новый объект модели в базе данных и возвращает его.

        Args:
            data (dict): Словарь с данными для создания объекта.

        Returns:
            DeclarativeBase: Созданный объект модели. Конкретный тип зависит от self.model.

        Raises:
            ValueError: Если переданные данные невалидны для модели
            SQLAlchemyError: При ошибках работы с базой данных
            Exception: Любые другие непредвиденные ошибки
        """
        try:
            instance = self.model(**data)
            self._session.add(instance)
            await self._session.commit()
            await self._session.refresh(instance)
            await self._session.aclose()
            return instance
        except Exception as e:
            await self._session.rollback()  # Откатываем изменения при других ошибках
            raise e

    async def _binary_expression_for_pk(self, data) -> List:
        """
        Получения бинарной экспрессии для sql запроса в базу данных.

        Args:
            data: dict

        Returns:
            list
        """
        result = []
        for col in self.model.__mapper__.columns:
            if col.name == self.model.__table__.primary_key.columns.keys()[0]:
                result.append(
                    col == data.get(self.model.__table__.primary_key.columns.keys()[0])
                )
        return result

    async def _update_object_form(self, data):
        """
        Обновляет объект модели в базе данных и возвращает его.

        Args:
            data (dict): Словарь с данными для создания объекта.

        Returns:
            DeclarativeBase: Созданный объект модели. Конкретный тип зависит от self.model.

        """
        sql_request = await self._binary_expression_for_pk(data)
        result = await self._session.execute(select(self.model).where(*sql_request))
        obj = result.scalar_one_or_none()
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            self._session.add(obj)
            await self._session.commit()
            await self._session.refresh(obj)
            await self._session.aclose()
            return obj
        else:
            data.pop(self.model.__table__.primary_key.columns.keys()[0])
            return await self._save_object_form(data)

    def update_field(
            self,
            model_field: str,
            widget: Type[AbstractWidget] | None = None,
            label: str | None = None,
            extra_attrs: ExtraAttrsDict | None = None,
            options_visible_value: str | None = None,
            validator: (
                    Callable[
                        [
                            Union[
                                str,
                                int,
                                float,
                                datetime.time,
                                datetime.date,
                                datetime.datetime,
                                UploadFile,
                            ]
                        ],
                        bool,
                    ]
                    | None
            ) = None,
    ) -> None:
        """
        Обновляет поле формы используя указанные аргументы.

        Args:
            model_field: Имя поля из модели для обновления
            widget: Виджет для поля
            label: Имя поля в форме
            extra_attrs: Словарь дополнительных атрибутов поля.
            options_visible_value: Видимое значения для поля select.
            validator: функция для валидации значений поля.
        Returns:
            None

        """
        if extra_attrs:
            for key in extra_attrs.keys():
                if key in ["required", "disabled", "readonly", "hidden", "value"]:
                    extra_attrs.pop(key)
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            if model_field != column.name:
                continue
            if widget is None:
                widget = asyncio.run(self._get_widget(column))
            attrs = asyncio.run(
                self._get_widget_attrs(
                    column, label, extra_attrs, options_visible_value
                )
            )
            self.fields[model_field] = widget(**attrs, name=column.name, validator=validator)

    async def _get_form_fields(self) -> None:
        """
        Метод, собирающий в словарь fields готовые объекты полей формы используя поля модели с учетом исключений.

        Returns:
            None
        """
        self.fields = {}
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            widget = await self._get_widget(column)
            attrs = await self._get_widget_attrs(column)
            self.fields[column.name] = widget(**attrs, name=column.name)

    async def _get_widget_attrs(
            self,
            column,
            label: str = None,
            extra_attrs: dict = None,
            options_visible_value: str = None,
    ) -> dict:
        """
        Генерирует атрибуты для виджетов полей формы на основе полей модели.

        Args:
            column:
            label:
            extra_attrs:
            options_visible_value:

        Returns:
            dict: словарь атрибутов
        """
        extensions = await self._get_filefield_extensions(column)
        options = await self._get_options_for_field_select(
            column, options_visible_value
        )
        attrs_dict = {
            "label": label if label else column.name,
            "readonly": True if column.name in self.readonly else False,
            "hidden": True if column.name in self.hidden else False,
            "required": True if not column.nullable else False,
            "disabled": True if column.name in self.disabled else False,
            "options": options,
            "extensions": extensions,
            "extra_attrs": extra_attrs if extra_attrs else {},
            "init_data": await self._get_init_data(column),
            "prefix": self.__dict__.get("prefix_form", None),
        }
        return attrs_dict

    async def _get_widget(self, column) -> Type[AbstractWidget]:
        """
        Получает виджет для поля формы в зависимости от типа поля модели.

        Args:
            column:
                колонка модели
        Returns:
            Type[AbstractWidget]:
                виджет в зависимости от типа поля модели
        """
        widget_dict = {
            PasswordField: PasswordWidget,
            "protect": PasswordWidget,
            "select": SelectWidget,
            "email": EmailWidget,
            String: TextWidget,
            Text: TextAreaWidget,
            Integer: IntegerWidget,
            Float: IntegerWidget,
            Numeric: IntegerWidget,
            Boolean: CheckboxWidget,
            FileField: FileWidget,
            Date: DateWidget,
            Time: TimeWidget,
            DateTime: DateTimeWidget,
            Enum: SelectWidget,
            enum.Enum: SelectWidget,
        }
        if (
                column.name in self.protect
                and not column.foreign_keys
                and column.type is not Boolean
        ):
            widget = widget_dict["protect"]
        elif column.foreign_keys:
            widget = widget_dict["select"]
        else:
            widget = widget_dict.get(column.type.__class__, TextWidget)
        return widget

    async def _get_init_data(self, column) -> dict:
        """
        Получает начальные значения для поля.

        Args:
            column:
                колонка модели.

        Returns:
            dict:
                словарь с данными.

        """
        result = {}
        if self._obj:
            if isinstance(self._obj, dict):
                result.update({column.name: self._obj.get(column.name, "")})
            else:
                result.update({column.name: self._obj.__dict__.get(column.name, "")})
            return result
        else:
            if column.default:
                result[column.name] = column.default.arg
            elif column.server_default:
                result[column.name] = column.server_default.arg
        return result

    async def _get_select_options_data(self, model) -> Sequence[DeclarativeBase]:
        """
        Запрашивает из базы данных значения для ForeignKeys.

        Args:
            model:
                модель базы данных для извлечения.

        Returns:
            list:
                список объектов.
        """
        if self._session:
            result = await self._session.scalars(select(model).options())
            await self._session.aclose()
            return result.all()
        return []

    async def _get_options_for_field_select(self, column, options_visible_value: str | None = None) -> dict:
        """
        Создает словарь опций для виджета select из модели.

        Args:
            column: колонка модели для которой создается список опций.
            options_visible_value: отображаемое в списке опций значение.

        Returns:
            dict: словарь значений
        """
        options_for_field = {}
        if self._session is None:
            return options_for_field
        if isinstance(column.type, Enum):
            return await self._get_option_for_enum_class(column)
        if not column.foreign_keys:
            return options_for_field
        for i in column.foreign_keys:
            select_objects = asyncio.run(
                self._get_select_options_data(
                    get_class_name_with_table_name(i.column.table.name)
                )
            )
            for obj in select_objects:
                pk_field = obj.__class__.__table__.primary_key.columns.keys()[0]
                options_for_field[str(obj.__dict__.get(pk_field))] = (
                    obj.__dict__.get(options_visible_value, obj)
                    if options_visible_value
                    else obj
                )
        return options_for_field

    async def selected_to_download(
            self, column, value, quantity: int = None
    ) -> Union[Sequence[DeclarativeBase], List]:
        """
        Перспективная функция. В разработке.

        Args:
            column:
            value:
            quantity:

        Returns:

        """
        if value:
            filter_from_where = column == value
            result = await self._session.scalars(
                select(self.model).where(*filter_from_where)
            )
        else:
            result = await self._session.scalars(select(self.model))
        if quantity:
            if quantity > 0:
                return result.all()[:quantity]
            return result.all()[quantity:]
        return result.all()

    @staticmethod
    async def _get_option_for_enum_class(column) -> dict:
        """
        Создает словарь опций для виджета select из класса Enum.

        Args:
            column:

        Returns:
            dict:
        """
        options_for_field = {}
        try:
            for value in column.type.enum_class:
                options_for_field[value.name] = value.value
            return options_for_field
        except Exception:
            for value in column.type.enums:
                options_for_field[value] = value
            return options_for_field

    @staticmethod
    async def _get_filefield_extensions(column):
        """
        Получает поддерживаемые расширения файлов для полей FileField.

        Args:
            column:

        Returns:
            list:
        """
        if isinstance(column.type, FileField):
            return column.type.allowed_extensions


class Form(BaseForm):

    def __init__(
            self,
            session: Optional[AsyncSession] = None,
            obj: Optional[Union[DeclarativeBase, dict]] = None,
            prefix_form: str = None,
    ):
        super().__init__()
        self.session = session
        self._obj = obj or None
        self.prefix_form = prefix_form
        for attr_name in vars(self.__class__):
            if attr_name.startswith("__"):
                continue
            attr = getattr(self.__class__, attr_name)
            if not isinstance(attr, BaseWidget):
                setattr(self, attr_name, copy.deepcopy(attr))
            if isinstance(attr, BaseWidget):
                self.fields[attr_name] = copy.deepcopy(attr)
                self.fields[attr_name].update_attrs(
                    obj=(
                        obj if isinstance(obj, dict) else obj.__dict__ if obj is not None else None
                    ),
                    prefix=prefix_form if prefix_form else None)

    def get_options(
            self,
            model: Union[Type[DeclarativeBase], Type[enum.Enum]],
            visible_value: str = None,
    ) -> Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int], dict]:
        """
        Метод добавления опций в поле select формы.

        Args:
            model:
            visible_value:

        Returns:

        """
        result = {}
        if isinstance(model, DeclarativeAttributeIntercept):
            if self.session:
                model_pk = model.__table__.primary_key.columns.keys()[0]
                objects = asyncio.run(self.session.scalars(select(model)))
                for obj in objects:
                    result[str(obj.__dict__.get(model_pk))] = obj.__dict__.get(visible_value, obj if visible_value else obj)
                asyncio.run(self.session.aclose())
                return result
            else:
                return result
        elif isinstance(model, enum.EnumMeta):
            objects = list(model)
            for obj in objects:
                try:
                    result[str(obj.name)] = obj.value
                except Exception:
                    result[str(obj.name)] = obj
            return result
        else:
            return result

    async def _add_checkbox_value(self, formated_data):
        """
        Добавляет в словарь значение False для полей типа checkbox при их отсутствии.

        Args:
            formated_data: dict

        Returns:
            dict
        """
        for field, widget in self.fields.items():
            if widget.type is bool:
                if field not in formated_data:
                    formated_data[field] = False
        return formated_data

    async def is_valid(self, form_data):
        self._obj = {}
        self.errors = {}
        cleaned_data = await self._cleaned_form(form_data)
        for field_name, field_value in cleaned_data.items():
            if field_name not in self.fields:
                continue
            is_valid = self.fields[field_name].default_validator(field_value)
            if not is_valid:
                self.errors[field_name] = ', '.join(map(str, self.fields[field_name].list_error))
                continue
            self._obj[field_name] = field_value
        return len(self.errors) == 0


__all__ = ('ModelForm', 'Form')