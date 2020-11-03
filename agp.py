#!/usr/bin/env python

from dataclasses import MISSING, dataclass, fields, is_dataclass
from numbers import Number
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Sequence,
    Set,
    Text,
    Tuple,
    TypeVar,
    cast,
)


@dataclass(frozen=True)
class Test:
    a: int
    b: Tuple[int, int, int]
    c: Set[int]


D = TypeVar("D")

SEQ_MAPPING = {
    Sequence: tuple,
    Tuple: tuple,
    Set: set,
    List: list,
}


def check_type(typ: type, obj: Any) -> bool:
    if isinstance(obj, typ):
        return True
    else:
        return False


def deserialize(typ: type, obj: Any) -> D:
    if is_dataclass(typ):
        if not isinstance(obj, Dict):
            raise ValueError()
        else:
            obj = cast(Dict, obj)

            def mk_args() -> Iterator[Tuple[str, Any]]:
                for field in fields(typ):
                    if field.init:
                        name = field.name
                        if name in obj:
                            val = obj[name]
                            if is_dataclass(typ):
                                yield name, deserialize(typ, obj=val)
                            elif check_type(typ, obj=val):
                                yield name, val
                            else:
                                raise ValueError()
                        elif field.default_factory != MISSING:
                            yield name, field.default_factory()
                        elif field.default != MISSING:
                            yield name, field.default
                        else:
                            raise KeyError(f"key of {typ}: {name} not in {obj}")

            args = {k: v for k, v in mk_args()}
            return typ(**args)

    elif check_type(typ, obj=obj):
        return obj

    else:
        raise ValueError(f"Unserializable type - {typ}")


a = Set[int]
b = Tuple[a, str]
print(b)
