import inspect
import types
import typing
from functools import lru_cache


def full_annotations(obj) -> dict:
    annot = {}
    type_obj = obj
    if not isinstance(obj, type):
        type_obj = type(obj)
    for dt in type_obj.mro()[::-1][1:]:
        annot.update(dt.__annotations__)
    return annot


@lru_cache
def get_origin_type(obj) -> type:
    """
    Пытается получить оригинальный тип переданного типа или объекта
    Parameters
    ----------
    obj : Объект или тип для анализа

    Returns
    -------

    """
    # TODO: Доработать для поддержки дженериков
    if type(obj) == str:
        for stack in inspect.stack():
            if obj in stack.frame.f_globals:
                obj = stack.frame.f_globals[obj]
                break
    return obj


def subdict(origin: dict, keys: str) -> dict:
    """
    Создает словарь из origin, ограниченный переданными ключами
    Parameters
    ----------
    origin : Исходный словарь
    keys : Ключи подсловаря в виде строки "ключ1,ключ2,..."

    Returns
    -------

    """
    return {key: value for key, value in origin if key in keys.split(",")}


def to_locals(depth: int = 1, /, **kwargs) -> None:
    """
    Первый ключевой аргумент возвращает (можно использовать как выражение).
    Изменяет локальный словарь стека вызова на глубине depth на значения ключевых параметров:

    Parameters
    ----------
    depth : Глубина стека вызова, 1 - стек вызывающей to_locals функции
    kwargs :

    Returns
    -------

    """
    if len(kwargs) == 0:
        return
    if depth < 1:
        raise ValueError("Глубина стека вызова не меньше 1")
    frame = inspect.stack()[depth].frame
    frame.f_locals.update(kwargs)


def as_exp(**kwargs) -> ...:
    """
    Первый ключевой аргумент возвращает его значение (можно использовать как выражение),
    все аргументы помещает в локальные переменные контекста вызова:

    print(as_exp(f=4,c=5))
    4
    print(f,c)
    4 5

    Parameters
    ----------
    kwargs :

    Returns
    -------

    """
    if len(kwargs) == 0:
        raise ValueError("Не передан ни один параметр")
    frame = inspect.stack()[1].frame
    frame.f_locals.update(kwargs)
    return next(iter(kwargs.values()))


def args_asdict(
    rename_key_map: dict[str, str | None] = None, kwargs_name="kwargs"
) -> dict:
    """
    Возвращает в виде словаря, все параметры переданые внешней функции
    Как правило, вызывается в первой строке тела анализируемой функции
    Parameters
    ----------
    rename_key_map : object
        Карта переимования ключей результирующего словаря из replace_key_map.key в replace_key_map.value,
        если replace_key_map.value is None - удаление ключа
    Returns
    -------

    """
    if rename_key_map is None:
        rename_key_map = {}
    frame = inspect.stack()[1].frame
    local = dict(frame.f_locals)
    kwargs = {}
    if local.get(kwargs_name):
        kwargs = local.pop(kwargs_name)
    kwargs.update(local)
    for key, new_key in rename_key_map.items():
        if key in kwargs:
            value = kwargs.pop(key)
            if value is not None and new_key is not None:
                kwargs[new_key] = value
    return kwargs


def partial(fn, *args, **kwargs):
    def inner(*in_args, **in_kwargs):
        new_args = args + in_args
        new_kwargs = kwargs | in_kwargs
        return fn(*new_args, **new_kwargs)

    return inner
