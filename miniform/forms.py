import asyncio
import copy
import enum
import json

import nest_asyncio
from typing import Sequence, Type, List, Optional, Literal, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper, DeclarativeBase
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept
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
    inspect,
)

from miniform.fields import *
from miniform.widgets import *
from miniform.utils import get_class_name_with_table_name


class BaseForm:
    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._session: Optional[AsyncSession] = None
        self._obj: Optional[Union[DeclarativeBase, dict]] = None
        self.csrf_token: dict = {}
        self.valid: bool

    def __str__(self) -> str:
        """
        :return: str
        """
        form_fieldset = (
                (
                    f"<input type='hidden' name='{list(self.csrf_token.keys())[0]}' value='{list(self.csrf_token.values())[0]}'/>\n" if self.csrf_token else "")
                + "<fieldset>\n"
                + ("".join(f"{field}" for field in self.fields.values()))
                + "</fieldset>\n"
        )
        return form_fieldset

    def form_dict(self):
        data = {}
        if self.csrf_token:
            data.update(self.csrf_token)
        for field, widget in self.fields.items():
            data.update(widget.get_data_to_dict())
        return data

    def form_json(self, indent=None, ensure_ascii=None):
        return json.dumps(self.form_dict(), indent=indent if indent else None,
                          ensure_ascii=ensure_ascii if ensure_ascii else False)

    def __getitem__(self, item) -> AbstractWidget:
        if item in self._fields:
            return self._fields[item]
        raise AttributeError(f'"{item}" is not a attribute in class {self.__class__}')

    def __getattr__(self, item) -> AbstractWidget:
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


class ModelForm(BaseForm):
    model: Type[DeclarativeBase] = None
    disabled = []
    exclude = []
    protect = []
    hidden = []
    readonly = []

    def __init__(
            self,
            session: Optional[AsyncSession] = None,
            obj: Optional[Union[DeclarativeBase, dict]] = None,
            csrf_token: dict = None,
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
        self._obj = obj if isinstance(obj, dict) else obj.__dict__ if obj is not None else None
        self.csrf_token = csrf_token or None
        self.valid: bool = False
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

    async def cleaned_form(self, form_data, to_format: bool = False) -> Dict:
        """
        Метод приведения данных в требуемый формат и удаления пустых значений из словаря.
        :param form_data:
        :param to_format: bool, default True
        :return: dict
        """
        if to_format is True:
            form_data = await self._convert_to_required_format(form_data)
        form_data = {
            key: value
            for key, value in form_data.items()
            if value not in [None, "", [], (), {}]
        }
        form_data = await self._cleaned_checkbox_data(form_data)
        return form_data

    async def is_valid(self, form_data):
        self._obj = {}
        cleaned_data = await self.cleaned_form(dict(form_data.multi_items()), to_format=True)
        for key, value in cleaned_data.copy().items():
            if key not in self.fields.keys():
                cleaned_data.pop(key)
                continue
            self._obj[key] = cleaned_data[key]
            err = self.fields[key].default_validator(cleaned_data[key])
            if err is not True:
                self.errors[key] = err
        if self.errors:
            await self._get_form_fields()
            return False

        return True

    async def save_form(
            self,
    ) -> DeclarativeBase:
        """
        Метод записи полученных данных из формы в базу данных.
        :param form_data:
        :return:
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

    async def _get_sql_request(self, data) -> List:
        result = []
        for col in self.model.__mapper__.columns:
            if col.name == self.model.__table__.primary_key.columns.keys()[0]:
                result.append(
                    col == data.get(self.model.__table__.primary_key.columns.keys()[0])
                )
        return result

    async def _update_object_form(self, data):
        sql_request = await self._get_sql_request(data)
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

    async def _cleaned_checkbox_data(self, formated_data):
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            if isinstance(column.type, Boolean):
                if column.name not in formated_data:
                    formated_data[column.name] = False
        return formated_data

    async def _convert_to_required_format(self, data: dict) -> dict:
        converted_data = {}
        for field, value in data.items():
            try:
                converted_value = self.fields[field].convert(value)
                converted_data[field] = converted_value
            except Exception:
                converted_data[field] = value
        return converted_data

    def update_field(
            self,
            field: str,
            widget: Type[AbstractWidget] = None,
            label: str = None,
            extra_attrs: dict = None,
            options_visible_value: str = None,
            validator=None
    ) -> None:
        """
        Метод, позволяющий изменить стандартный виджет поля.
        :param field: str - Обязательный атрибут. Имя поля.
        :param widget: Type[BaseFormInputField] - Необязательный атрибут. Класс виджета для замены стандартного.
        :param label: str - Необязательный атрибут. Строка, которая заменить имя поля в <label>.
        :param extra_attrs: dict - Необязательный атрибут. Параметры, которые будут добавлены в <input>.
        :return: None
        """
        if extra_attrs:
            for key in extra_attrs.keys():
                if key in ["required", "disabled", "readonly", "hidden", "value"]:
                    extra_attrs.pop(key)
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            if field != column.name:
                continue
            if widget is None:
                widget = asyncio.run(self._get_widget(column))
            attrs = asyncio.run(self._get_widget_attrs(column, label, extra_attrs, options_visible_value))
            self.fields[field] = widget(**attrs, name=column.name, validator=validator)

    async def _get_form_fields(self) -> None:
        """
        Метод, собирающий в словарь fields готовые объекты полей формы используя поля модели с учетом исключений.
        :return: None
        """
        mapper = class_mapper(self.model)
        for column in mapper.columns:
            if column.name in self.exclude:
                continue
            widget = await self._get_widget(column)
            attrs = await self._get_widget_attrs(column)
            self.fields[column.name] = widget(**attrs, name=column.name)

    async def _get_widget_attrs(
            self, column, label: str = None, extra_attrs: dict = None, options_visible_value: str = None
    ) -> dict:
        """
        Метод генерирует атрибуты для виджетов полей формы на основе полей модели.
        :param column: ColumnElement - обязательный атрибут, поле модели
        :return: dict - словарь атрибутов для виджета.
        """
        extensions = await self._get_filefield_properties(column)
        options = await self._get_options_for_field_select(column, options_visible_value)
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
            "error": self.errors.get(column.name) if self.errors.get(column.name) else ""
        }
        return attrs_dict

    async def _get_widget(self, column) -> Type[AbstractWidget]:
        """
        Метод возвращает виджет для поля формы в зависимости от поля модели.
        :param column: ColumnElement - обязательный атрибут, поле модели
        :return: Type[BaseFormInputField]
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
        Метод генерирует начальные данные для поля.
        :param column: ColumnElement - поле модели, обязательный атрибут.
        :return: dict - Возвращает словарь с начальными данными для поля формы.
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
        :param model: DeclarativeBase
        :return: Sequence[DeclarativeBase]
        """
        if self._session:
            result = await self._session.scalars(select(model).options())
            await self._session.aclose()
            return result.all()
        return []

    async def _get_options_for_field_select(self, column, options_visible_value: str = None) -> dict:
        """
        Создает словарь опций для виджета select из модели.
        :param column: ColumnElement - поле модели, обязательный атрибут.
        :return: dict - словарь с опциями
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
                options_for_field[str(obj.__dict__.get(pk_field))] = obj.__dict__.get(options_visible_value,
                                                                                      obj) if options_visible_value else obj
        return options_for_field

    async def selected_to_download(
            self, column, value, quantity: int = None
    ) -> Union[Sequence[DeclarativeBase], List]:
        """
        *** Перспективная функция. В разработке ***
        Загружает выборку объектов из базы данных.
        :param column: ColumnElement
        :param value: Any
        :param quantity: Optional[int]
        :return: list
        """
        if value:
            filter_from_where = await self._get_sql_for_selected_to_download(
                column, value
            )
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
    async def _get_sql_for_selected_to_download(column, value):
        result = []
        request = column == value
        result.append(request)
        return result

    async def _get_option_for_enum_class(self, column):
        """
        Создает словарь опций для виджета select из класса Enum.
        :param column: ColumnElement - поле модели, обязательный атрибут.
        :return: dict - словарь с опциями
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
    async def _get_filefield_properties(column):
        if isinstance(column.type, FileField):
            return column.type.allowed_extensions


class Form(BaseForm):

    def __init__(
            self,
            session: Optional[AsyncSession] = None,
            obj: Optional[Union[DeclarativeBase, dict]] = None,
            prefix_form: str = None,
            csrf_token: dict = None
    ):
        super().__init__()
        self.session = session
        self._obj = obj or None
        self.prefix_form = prefix_form
        self.csrf_token = csrf_token
        # self._fields: dict = {}
        for attr_name in vars(self.__class__):
            if attr_name.startswith("__"):
                continue
            attr = getattr(self.__class__, attr_name)
            if not isinstance(attr, BaseWidget):
                setattr(self, attr_name, copy.deepcopy(attr))
            if isinstance(attr, BaseWidget):
                self.fields[attr_name] = copy.deepcopy(attr)
                self.fields[attr_name].update_attrs(
                    obj=self._obj if self._obj else {},
                    prefix=prefix_form if prefix_form else None,
                )

    def get_options(
            self, model: Union[Type[DeclarativeBase], Type[enum.Enum]], visible_value: str = None
    ) -> Union[dict[str, str], dict[int, str], dict[int, int], dict[str, int], dict]:
        """
        Метод добавления опций в поле select формы
        :param model: Type[DeclarativeBase] or Type[enum.Enum] - обязательный атрибут
        :param visible_value: str - имя поля для отображения в выпадающем списке
        :return: dict - словарь с данными
        """
        result = {}
        if isinstance(model, DeclarativeAttributeIntercept):
            if self.session:
                model_pk = model.__table__.primary_key.columns.keys()[0]
                objects = asyncio.run(self.session.scalars(select(model)))
                for obj in objects:
                    result[obj.__dict__.get(model_pk)] = obj.__dict__.get(visible_value, obj) if visible_value else obj
                asyncio.run(self.session.aclose())
                return result
            else:
                return result
        elif isinstance(model, enum.EnumMeta):
            objects = list(model)
            for obj in objects:
                try:
                    result[obj.name] = obj.value
                except Exception:
                    result[obj.name] = obj
            return result
        else:
            return result

    def cleaned_form(self, form_data) -> dict:
        result = {}
        for key, value in dict({**form_data}):
            if key in self.fields.keys():
                result[key] = value
        return result


class FormSet:
    _parent_form = None
    _parent_obj = None
    _child_form = None
    _session = None
    _child_load = None
    form = None

    def __init__(
            self,
            parent_form,
            child_form,
            session=None,
            parent_obj=None,
            quantity_child_obj: Union[int, Literal["__all__"]] = None,
            quantity_child_form=None,
            child_load: bool = False,
    ):
        self.child_formset = []
        self._session = session
        self._parent_form = parent_form
        self._parent_obj = parent_obj or None
        self._child_form = child_form
        self._quantity_child_obj = quantity_child_obj or 1
        self._quantity_child_form = quantity_child_form or 1
        self._child_load = (
            child_load if getattr(self._child_form, "model", None) else False
        )
        setattr(self, "form", parent_form(session=session, obj=parent_obj))
        asyncio.run(self._get_child_formset())

    def __str__(self):
        return asyncio.run(self.render_all())

    def __getitem__(self, item):
        if item == "formset":
            return self.child_formset
        if item in self.__dict__:
            return self.__dict__[item]

    async def render_all(self) -> str:
        parent = await self.render_parent_form()
        child = await self.render_child_formset()
        return f"{parent}<hr>\n{child}"

    async def render_parent_form(self):
        return self.form

    async def render_child_formset(self):
        html = ""
        for form in self.child_formset:
            html += str(form)
            html += "<hr>"
        return html

    """ Обработка формы. Закончить!"""

    async def cleaned_form(self, form_data) -> dict:
        """
        Обработка данных формы
        :param form_data: starlette.datastructures.FormData
            данные из формсета
        :return: dict
            result = {"parent": {}, "children": []}
        """
        form_class_name = self._child_form.__name__.lower()
        result = {"parent": {}, "children": []}
        for key in list(self.form.fields.keys()):
            if key in dict(form_data):
                result["parent"][key] = dict(form_data)[key]
        for i in range(1, self._quantity_child_form + 1):
            child_data = {}
            prefix = f"{form_class_name}-{i}_"
            for key, value in form_data.items():
                if key.startswith(prefix):
                    child_data[key.replace(prefix, "")] = value
            result["children"].append(child_data)
        return result

    async def save_form(self):
        pass

    async def save_formset(self):
        pass

    async def _get_child_formset(self) -> None:
        """
        Генерирует список self.child_formset в зависимости от атрибутов класса.
        :return: None
        """
        if self._child_load is True:
            child_objects = await self._get_objects_for_child_form()
            for i, obj in enumerate(child_objects, 1):
                child = self._child_form(
                    session=self._session,
                    obj=obj,
                    prefix_form=f"{self._child_form.__name__.lower()}-{i}",
                )
                self.child_formset.append(child)
        else:
            for i in range(1, self._quantity_child_form + 1):
                self.child_formset.append(
                    self._child_form(
                        session=self._session,
                        prefix_form=f"{self._child_form.__name__.lower()}-{i}",
                    )
                )

    async def _get_objects_for_child_form(self):
        return await self._filter_child_selected_to_download(
            self._get_fk_field(),
            self._parent_obj.__dict__.get(self._get_model_field_for_fk()),
        )

    async def _filter_child_selected_to_download(self, column, value) -> List:
        """
        Возвращает список объектов для дочерних форм формсета.
        :param column: ColumnElement - поле, по которому будет выборка объектов из базы данных.
        :param value: int - значение поля для выборки
        :return: list
        """
        sql_request = await self._get_sql_request_for_filter(column, value)
        result = await self._session.scalars(
            select(self._child_form.model).where(*sql_request)
        )
        await self._session.close()
        if self._quantity_child_obj == "__all__":
            return result.all()
        elif self._quantity_child_obj > 0:
            return result.all()[: self._quantity_child_obj]
        elif self._quantity_child_obj < 0:
            return list(reversed(result.all()))[self._quantity_child_obj:]

    def _get_fk_field(self):
        """
        Возвращает колонку с foreign_key к модели из родительской формы
        :return:
        """
        mapper = inspect(self._child_form.model)
        for column in mapper.columns:
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    if fk.column.table.name == self._parent_form.model.__table__.name:
                        return column

    def _get_model_field_for_fk(self):
        """
        Возвращает имя поля из модели родительской формы к которому привязан foreign_key
        :return:
        """
        mapper = inspect(self._child_form.model)
        for foreign_key in mapper.local_table.foreign_keys:
            # Проверяем, ссылается ли внешний ключ на таблицу model1
            if foreign_key.column.table.name == self._parent_form.model.__table__.name:
                return foreign_key.column.name  # Возвращаем имя поля с внешним ключом

    @staticmethod
    async def _get_sql_request_for_filter(column, value):
        result = []
        request = column == value
        result.append(request)
        return result


__all__ = ('ModelForm', 'Form', 'FormSet')