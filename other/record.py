import inspect
from datetime import datetime
from functools import partial

import dateutil.parser

from dataclasses import MISSING
from typing import TypeVar
from utils import get_origin_type
import enum


class T_MissingKeyBehavior(enum.Enum):
    store_as_attr = enum.auto()
    store_as_internal = enum.auto()


class T_MissingFieldBehavior(enum.Enum):
    store_as_MISSING = MISSING
    store_as_None = None


T = TypeVar("T")


def record(
    cls: type[T] = None,
    /,
    *,
    missing_key_behavior: T_MissingKeyBehavior = T_MissingKeyBehavior.store_as_attr,
    missing_field_behavior: T_MissingFieldBehavior = T_MissingFieldBehavior.store_as_MISSING,
    **kwargs,
):
    """

    Parameters
    ----------
    cls :
    missing_as_None :  Вместо MISSING назначать None
    missing_key_behavior : Ключи и значения словаря из fromdict(source, объекта, не нашедшие пару:
        "store_as_attr" - сохранять как атрибуты объекта, (по умолчанию)
        "store_as_internal" - сохранять в словаре атрибута объекта "__missing_keys__",
        иначе - игнорировать
    missing_field_behavior : Поля объекта, не нашедшие пару в ключах словаря из fromdict(source, :
        "store_as_MISSING" - сохранять, назначая им значение MISSING (по умолчанию)
        "store_as_None" - сохранять, назначая им значение None,
        иначе - удалять из объекта
    kwargs :

    Returns
    -------

    """
    _missing_key_behavior = missing_key_behavior
    _missing_field_behavior = missing_field_behavior
    # _params: dict[str] = {}
    _assign_fields = set()

    def fromdict(
        self: T,
        from_dict: dict[str],
    ) -> T:
        """

        Parameters
        ----------
        self : object
        """
        found_fields = set()
        annotations: dict[str] = self.__annotations__
        for key, value in from_dict.items():
            # Проходим по словарю
            if hasattr(self, key):
                # Атрибут уже установлен
                attr_value = getattr(self, key)
                if inspect.isdatadescriptor(attr_value):
                    _assign_fields.add(key)
                    setattr(self, key, attr_value)
            elif key_type := annotations.get(key, None):
                # Найдено соответствие в полях
                found_fields.add(key)
                key_type = get_origin_type(key_type)

                # if key in _params:
                #     # Поищем значение в дополнительных параметрах
                #     value = _params[key]
                if inspect.isdatadescriptor(key_type):
                    _value = key_type()
                    _value.__set_name__(self.__class__, key)
                    setattr(self, key, value)
                    _assign_fields.add(key)
                elif hasattr(key_type, "__is_record__"):
                    # _pparams = {}
                    # value: dict
                    for param_key, param_value in from_dict.items():
                        if (
                            len((chunks := param_key.split("."))) > 1
                            and chunks[0] == key
                        ):
                            value[".".join(chunks[1:])] = param_value
                            break
                    value = key_type(from_dict=value)
                elif callable(value):
                    value = value(value)
                elif not isinstance(value, key_type):
                    # Попытаемся привести тип
                    try:
                        if (key_type == datetime) and isinstance(value, str):
                            # value: str
                            value = dateutil.parser.parse(value)
                        else:
                            value = key_type(value)
                    except TypeError as err:
                        # print(err)
                        print({"value": value, "error": err})
                        # value
                        # raise err

                _assign_fields.add(key)
                setattr(self, key, value)
            elif _missing_key_behavior == T_MissingKeyBehavior.store_as_attr:
                _assign_fields.add(key)
                setattr(self, key, value)
            elif _missing_key_behavior == T_MissingKeyBehavior.store_as_internal:
                if not getattr(self, "__missing_keys__", None):
                    self.__missing_keys__ = {}
                self.__missing_keys__[key] = value

            _fields = set(annotations.keys())
            for field in _fields - found_fields:
                if hasattr(self, field):
                    # Поле уже имеет значение, не трогаем
                    _assign_fields.add(field)
                    continue
                if _missing_field_behavior == T_MissingFieldBehavior.store_as_MISSING:
                    _assign_fields.add(field)
                    setattr(self, field, MISSING)
                elif _missing_field_behavior == T_MissingFieldBehavior.store_as_None:
                    _assign_fields.add(field)
                    setattr(self, field, None)
        return self

    def __init__(
        self: T,
        from_dict: dict = None,
        # params: dict = None,
        missing_key_behavior: T_MissingKeyBehavior = None,
        missing_field_behavior: T_MissingFieldBehavior = None,
    ):
        nonlocal _missing_key_behavior, _missing_field_behavior
        if missing_key_behavior is not None:
            _missing_key_behavior = missing_key_behavior
        if missing_field_behavior is not None:
            _missing_field_behavior = missing_field_behavior
        # if params is not None:
        #     _params = params

        obj_fields: dict[str] = self.__annotations__
        for key, value in obj_fields.items():
            if hasattr(type(self), key):
                # Если атрибут на уровне класса,
                # делаем его копию на уровне объекта, чтобы не портить класс
                att_value = getattr(type(self), key)
                _assign_fields.add(key)
                setattr(self, key, att_value)

        self.__is_record__["from_dict"] = from_dict
        # self.__is_record__["params"] = params
        fromdict(self, from_dict=from_dict)
        if hasattr(self, "__post_init__") and callable(self.__post_init__):
            self.__post_init__()

    def __fields__(self):
        return {key: getattr(self, key) for key in dir(self) if not key.startswith("_")}

    def __repr__(self):
        # fld = self.__fields__()
        return (
            f"{cls.__name__}: ("
            + f", ".join(
                (
                    f"{key}:{repr(getattr(self, key))}"
                    for key in dir(self)
                    if not key.startswith("_")
                )
            )
            + ")"
        )

    if cls is None:
        return partial(
            record,
            missing_key_behavior=_missing_key_behavior,
            missing_field_behavior=_missing_field_behavior,
            **kwargs,
        )

    cls.__is_record__ = {}
    cls.__init__ = __init__
    cls.__repr__ = __repr__
    cls.__fields__ = __fields__
    return cls


if __name__ == "__main__":

    @record
    class UserInfo:
        country: str
        login: str
        display_name: str
        uid: str

    @record
    class DiskInfo:
        max_file_size: int
        paid_max_file_size: int
        total_space: int
        trash_size: int
        is_paid: bool
        used_space: int
        system_folders: dict[str, str]
        user: UserInfo
        new_name: str

    source = {
        "max_file_size": 53687091200,
        "paid_max_file_size": 53687091200,
        "total_space": 2289217568768,
        "trash_size": 0,
        "is_paid": True,
        "used_space": 113218319704,
        "system_folders": {
            "odnoklassniki": "disk:/Социальные сети/Одноклассники",
            "google": "disk:/Социальные сети/Google+",
            "instagram": "disk:/Социальные сети/Instagram",
            "vkontakte": "disk:/Социальные сети/ВКонтакте",
            "attach": "disk:/Почтовые вложения",
            "mailru": "disk:/Социальные сети/Мой Мир",
            "downloads": "disk:/Загрузки/",
            "applications": "disk:/Приложения",
            "facebook": "disk:/Социальные сети/Facebook",
            "social": "disk:/Социальные сети/",
            "messenger": "disk:/Файлы Мессенджера",
            "calendar": "disk:/Материалы встреч",
            "scans": "disk:/Сканы",
            "screenshots": "disk:/Скриншоты/",
            "photostream": "disk:/Фотокамера/",
        },
        "user": {
            "country": "ru",
            "login": "kale-ru",
            "display_name": "Александр",
            "uid": "56091251",
        },
        "unlimited_autoupload_enabled": True,
        "revision": "1675185477609069",
        "new_revision": 1675185477609069,
    }

    base = DiskInfo(source, missing_field_behavior=T_MissingFieldBehavior.store_as_None)

    print(base)
