import dataclasses

from dataclasses import dataclass, MISSING, field, InitVar, fields
from typing import Any, ForwardRef, Callable, Self, TypeVar, Generic, Type
from functools import partial, wraps
import inspect

__DICT_SOURCE__ = "_dict_source_"


Cls = TypeVar("Cls")
Obj = TypeVar("Obj")


def record(
    cls=None,
    /,
    dict_source: Callable[..., dict[str, Any]] = None,
    **kwargs,
):

    if cls is None:
        return partial(record, **kwargs)

    def __post_init__(self, *args, **kwargs):
        nonlocal origin__post_init__
        if callable(origin__post_init__):
            origin__post_init__(self, *args, **kwargs)

    def __getattr__(self, name: str):
        nonlocal origin__getattr__
        if callable(origin__getattr__):
            origin__getattr__(self, name)

        if attr_type := self.__annotations__.get(name, None):
            # Есть в аннотиции, но нет в аттрибутах: не нашлось начального значения
            # field_type = cls_fields[name]
            if callable(attr_type):
                params_spec = inspect.signature(attr_type).parameters
                params = [self, name]
                value = attr_type(*(params[: len(params_spec)]))
                object.__setattr__(self, name, value)
                return value

            return MISSING
        else:
            raise ValueError(f"attribute {name} not found")

    def __setattr__(self, key, value):
        nonlocal origin__setattr__
        if callable(origin__setattr__):
            origin__setattr__(self, key, value)
        if attr_type := self.__annotations__.get(key, None):
            if type(attr_type) == str:
                attr_type = globals()[attr_type]
            if isinstance(attr_type, dataclasses.InitVar):
                attr_type = attr_type.type
            value = attr_type(value)
            object.__setattr__(self, key, value)
        else:
            raise ValueError(f"attribute {key} not found")

    cls = dataclass(cls, **kwargs)

    # cls_fields: dict[str, type] = {name: cls.__annotations__[name] for name in fields(cls)}
    origin__getattr__ = getattr(cls, "__getattr__", None)
    cls.__getattr__ = __getattr__
    origin__setattr__ = getattr(cls, "__setattr__", None)
    cls.__setattr__ = __setattr__
    origin__post_init__ = getattr(cls, "__post_init__", None)
    cls.__post_init__ = __post_init__

    return cls


def record_from(cls=None, /, **kwargs):

    if cls is None:
        return partial(record, **kwargs)

    def __getattr__(self, name: str):
        if self.__annotations__.get(name, None):
            # Есть в аннотиции, но нет в аттрибутах: не нашлось начального значения
            return MISSING
        else:
            raise ValueError(f"attribute {name} not found")

    def __setattr__(self, key, value):
        if attr_type := self.__annotations__.get(key, None):
            if type(attr_type) == str:
                attr_type = globals()[attr_type]
            if isinstance(attr_type, dataclasses.InitVar):
                attr_type = attr_type.type
            value = attr_type(value)
            object.__setattr__(self, key, value)
        else:
            raise ValueError(f"attribute {key} not found")

    cls.__getattr__ = __getattr__
    cls.__setattr__ = __setattr__
    return dataclass(cls, **kwargs)


def record(cls=None, /, *, MISSING_is_None=False, **kwargs):
    """
    Декоратор изменяющий поведение dataclass, сохраняя все поля в экземпляре класса. Стандартное поведение dataclass,
    подразумевает удаление из декорируемого класса полей с типами, которые не имеют непосредственно
    (либо через поле default функции field) заданного начального значения (автоматически генерируемого в параметрах __init__),
    и поле default_factory функции имеет MISSING (значение поля не формируется в процессе исполнения __init__).
    Декоратор изменяет это поведение, сохраняя ВСЕ поля с типами. В случае отсутствия вышеупомянутых вариантов присвоения
    начального значения полю, значение поля устанавливается в MISSING (либо в None,
    если параметр декоратора MISSING_is_None=True). Таким образом, структура становится более предсказуемой
    для программиста, что позволяет избежать runtime ошибок, из-за отсутствия в структуре ожидаемого поля.
    Также, расширена трактовка значения поля default_factory функции field. Если установленное значение
    имеет callable природу, и количество обязательных его параметров равно одному или двум, то при создании экземпляра класса
    декоратор пытается вызвать значение default_factory с параметрами "значение инициализируемого экземпляра (self)",
    и "имя инициализиремого поля" (если два параметра). Если вызов успешен, и тип значения результата вызова совпадает
    с типом инициализируемого поля, это значение присваивается инициализируемому полю.
    Если результат вызова имеет тип tuple (или совместимый), или dict (или совместимый),
    считается что это значения для параметров конструктора типа инициализируемого поля,
    и производится попытка создания экземпляра этого типа с параметрами из результата этого
    вызова. В случае неудачи, значение поля устанавливается в MISSING (либо в None, если параметр декоратора
    MISSING_is_None=True)

    field(default_factory= callable(объект,имя_поля)), где callable будут переданы следующие параметры:

    объект - значение текущего объекта декорируемого класса

    имя_поля - собственно, имя поля.

    callable должен вернуть либо готовый экземляр класса, либо tuple, либо dict с параметрами
    для конструктора экземпляра.
    Например,

    # Если конструктор Volume имеет один обязательный параметр, будет создан экземпляр Volume
    volume:Volume

    # Будет создан экземпляр int
    speed:int

    # Непосредственное создание экземпляра:
    color:Color = field(default_factory=lambda obj,name : Color(obj.rgb, name))

    # Передача в кортеже параметров конструктора декоратору, для создания экземпляра:
    color:Color = field(default_factory=lambda obj,name : (obj.rgb, name))

    # Передача в словаре параметров конструктора декоратору, для создания экземпляра:
    color:Color = field(default_factory=lambda obj,name : {'value':obj.rgb,'color_name':name})

    Parameters
    ----------

    Returns
    -------

    """

    __origin__post_init__: Callable | None = None
    init_fields: dict[str, Any] = {}

    def __post_init__(self, *args, **kwargs):

        for _attr_name, _attr_value in init_fields.items():
            if getattr(self, _attr_name, MISSING) != MISSING:
                # значение аттрибута экземпляра уже установлено
                continue
            _attrs = dict(cls.__annotations__.items())
            _attr_type: type = _attrs.get(_attr_name, None)
            if callable(_attr_value):
                _value = _attr_value(self, _attr_name)
                if not isinstance(_value, _attr_type):
                    # Если тип результата lambda не совпадает с типом поля,
                    # возможно возвращены параметры для конструктора типа
                    if isinstance(_value, Sequence):
                        _value = _attr_type(*_value)
                    elif isinstance(_value, Mapping):
                        _value = _attr_type(**_value)
            else:
                _value = _attr_value

            if _value is MISSING and MISSING_is_None:
                _value = None

            setattr(self, _attr_name, _value)

        if callable(__origin__post_init__):
            __origin__post_init__(self, *args, **kwargs)

    def preprocess_class(cls):
        """
        Убирает нестандартные для dataclasses поля из найденных field, и сохраняет их
        для дальнейшей обработки в __post_init__, инициализурует поля field(init=False
        запоминает их, для дальнейшей обработки в __post_init__
        Parameters
        ----------
        cls :

        Returns
        -------

        """
        items = dict(cls.__annotations__.items())
        # items.
        # _attr_exist = items.get(mapfield) is not None
        # _attr_found = False

        for attr_name, attr_type in items.items():
            # Обрабатываемые поля начинаются после поля _field
            # if _attr_exist and not _attr_found:
            #     if attr_name == mapfield:
            #         _attr_found = True
            #     continue
            _processed = True
            # _new_field_attr = {"init": False}

            new_field_value = {"init": False}

            if (attr_value := getattr(cls, attr_name, MISSING)) is not MISSING:
                # назначено ли начальное значение
                if isinstance(attr_value, dataclasses.Field):
                    # назначен инфокласс Field
                    if callable(attr_value.default_factory):
                        # Обработка lambda data_factory
                        f_lambda = attr_value.default_factory
                        sign = inspect.signature(f_lambda)
                        if len(sign.parameters) == 3:
                            # Убрать и запомнить для __pos_init__
                            init_fields[attr_name] = f_lambda
                            new_field_value["default_factory"] = MISSING
                elif issubclass(
                    attr_type,
                    (
                        typing.Sequence,
                        typing.Set,
                        typing.Mapping,
                        typing.Collection,
                    ),
                ):
                    new_field_value["default_factory"] = type(attr_value)
                # elif isinstance(attr_value, (int, float, str, bool, tuple)):
                else:
                    new_field_value["default"] = attr_value

                for name, value in new_field_value.items():
                    setattr(attr_value, name, value)

            else:
                # Атрибуту не назначено начальное значение,
                # значит, значение будет определяться в __post_init__
                attr_value = field(init=False)

            setattr(cls, attr_name, attr_value)

        return cls

    def postprocess_class(cls):
        nonlocal __origin__post_init__
        __origin__post_init__ = getattr(cls, "__post_init__", None)
        cls.__post_init__ = __post_init__
        return cls

    if cls is None:
        return partial(dataclass_map, MISSING_is_None=MISSING_is_None, **kwargs)

    cls = preprocess_class(cls)
    cls = dataclass(cls, **kwargs)
    return postprocess_class(cls)


def dataclass_map(cls=None, /, *, mapfield: str = None, MISSING_is_None=False, **kwargs):
    """
    Декоратор расширяющий dataclass возможностью отображения поля mapfield типа Mapping на низлежащие
    с именами как у ключей mapfield. Если соответствие полей не найдено, и не определенно значение по умолчанию,
    полю присваивается значение MISSING (или None, если параметр декоратора MISSING_is_None=True)

    При создании экземпляра декорируемого класса в конструктор передаются имя поля mapfield
    и значения для полей до него, далее производится преобразование содержимого ключей mapfield
    в типы соответствующих полей декорируемого класса. При создании экземпляра типа поля,
    ожидается что его конструктор имеет один обязательный параметр, куда передается содержимое ключа
    одноименного с именем поля, из значения mapfield. Для типов с большим количеством
    обязательных полей в конструкторе, либо в других случаях, возможно использование функции

    field(default_factory= callable(объект,имя_поля,значение_поля)), где callable будут переданы следующие параметры:

    объект - значение текущего объекта декорируемого класса

    имя_поля - собственно, имя поля.

    значение_поля - содержимое ключа имя_поля из mapfield

    callable должен вернуть либо готовый экземляр класса, либо Sequence, либо Mapping с параметрами
    для конструктора экземпляра.
    Например,

    # Если конструктор Volume имеет один обязательный параметр, будет создан экземпляр Volume
    volume:Volume

    # Будет создан экземпляр int
    speed:int

    # Непосредственное создание экземпляра:
    color:Color = field(default_factory=lambda obj,name,value : Color(obj, name, value))

    # Передача в кортеже параметров конструктора декоратору, для создания экземпляра:
    color:Color = field(default_factory=lambda obj,name,value : (obj, name, value))

    # Передача в словаре параметров конструктора декоратору, для создания экземпляра:
    color:Color = field(default_factory=lambda obj,name,value : {'owner':obj,'field_name':name,'value':value})

    Parameters
    ----------
    mapfield : имя поля типа Mapping, с отображаемыми данными

    Returns
    -------

    """
    __origin__post_init__: Callable | None = None

    lambdas: dict[str, Callable] = {}

    def __post_init__(self, *args, **kwargs):
        items = dict(self.__annotations__.items())
        _mapfield: dict[str, Any] = getattr(self, mapfield)
        if not isinstance(_mapfield, Mapping):
            raise ValueError(f"Field '{mapfield}' must by Mapping type")
        _field_exist = items.get(mapfield) is not None
        _field_found = False
        for _attr_name, _attr_type in items.items():
            # Обрабатываемые поля начинаются после поля _field
            if _field_exist and not _field_found:
                if _attr_name == mapfield:
                    _field_found = True
                break

            _map_value = _mapfield.get(_attr_name, MISSING)

            if _callable := lambdas.get(_attr_name):
                _value = _callable(self, _attr_name, _map_value)
                if not isinstance(_value, _attr_type):
                    # Если тип результата lambda не совпадает с типом поля,
                    # возможно возвращены параметры для конструктора типа
                    if isinstance(_value, Sequence):
                        _value = _attr_type(*_value)
                    elif isinstance(_value, Mapping):
                        _value = _attr_type(**_value)
            else:
                _value = _map_value

            if _value is MISSING and MISSING_is_None:
                _value = None

            setattr(self, _attr_name, _value)

        if callable(__origin__post_init__):
            __origin__post_init__(self, *args, **kwargs)

    _processed = False

    def preprocess_class(cls):
        """
        Убирает нестандартные для dataclasses поля из найденных field, и сохраняет их
        для дальнейшей обработки в __post_init__, инициализурует поля field(init=False
        Parameters
        ----------
        cls :

        Returns
        -------

        """
        items = dict(cls.__annotations__.items())
        # items.
        _attr_exist = items.get(mapfield) is not None
        _attr_found = False

        for attr_name, attr_type in items.items():
            # Обрабатываемые поля начинаются после поля _field
            if _attr_exist and not _attr_found:
                if attr_name == mapfield:
                    _attr_found = True
                continue
            _processed = True
            # _new_field_attr = {"init": False}

            new_field_value = {"init": False}

            if (attr_value := getattr(cls, attr_name, MISSING)) is not MISSING:
                # назначено ли начальное значение
                if isinstance(attr_value, dataclasses.Field):
                    # назначен инфокласс Field
                    if callable(attr_value.default_factory):
                        # Обработка lambda data_factory
                        f_lambda = attr_value.default_factory
                        sign = inspect.signature(f_lambda)
                        if len(sign.parameters) == 3:
                            # Убрать и запомнить для __pos_init__
                            lambdas[attr_name] = f_lambda
                            new_field_value["default_factory"] = MISSING
                elif issubclass(
                    attr_type,
                    (
                        typing.Sequence,
                        typing.Set,
                        typing.Mapping,
                        typing.Collection,
                    ),
                ):
                    new_field_value["default_factory"] = type(attr_value)
                # elif isinstance(attr_value, (int, float, str, bool, tuple)):
                else:
                    new_field_value["default"] = attr_value

                for name, value in new_field_value.items():
                    setattr(attr_value, name, value)

            else:
                # Атрибуту не назначено начальное значение,
                # значит, значение будет определяться в __post_init__
                attr_value = field(init=False)

            setattr(cls, attr_name, attr_value)

        return cls

    def postprocess_class(cls):
        nonlocal __origin__post_init__
        if hasattr(cls, "__post_init__"):
            __origin__post_init__ = getattr(cls, "__post_init__")
        # if _processed:
        cls.__post_init__ = __post_init__
        return cls

    if mapfield is None:
        raise ValueError("Argument '_field' cannot be empty")

    # def wrap(cls):
    #     return dataclass_map(_field=mapfield, MISSING_is_None=MISSING_is_None)

    if cls is None:
        return partial(dataclass_map, mapfield=mapfield, MISSING_is_None=MISSING_is_None, **kwargs)

    # args = (preprocess_class(cls),)
    # return postprocess_class(dataclass(*args, **kwargs))
    cls = preprocess_class(cls)
    cls = dataclass(cls, **kwargs)
    return postprocess_class(cls)


if __name__ == "__main__":

    @record
    class Disk:
        ...

    ...
