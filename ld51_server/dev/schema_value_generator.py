import math
import uuid
from random import Random
from typing import Any


class SchemaValueGenerator:
    _rng: Random
    _root_schema: dict[str, Any]

    def __init__(self, schema: dict[str, Any], *, seed: int | None = None) -> None:
        self._rng = Random(seed)
        self._root_schema = schema

    def _random_bool(self) -> bool:
        return bool(self._rng.getrandbits(1))

    def _random_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=self._rng.randbytes(16), version=4)

    def _ex_string(self, schema: dict[str, Any]) -> str:
        match schema:
            case {"format": "uuid"}:
                return str(self._random_uuid())
            case {"format": _}:
                return "string with unknown format"
            case _:
                return "string"

    def _ex_boolean(
        self,
    ) -> bool:
        return self._random_bool()

    def _get_inclusive_discrete_min_bound(
        self, schema: dict[str, Any], scale: float
    ) -> int | None:
        # dummy variable because of pylint
        # see: <https://github.com/PyCQA/pylint/issues/5327>
        value = None
        match schema:
            case {"minimum": value} if value is not None:
                return math.ceil(value * scale)
            case {"exclusiveMinimum": value} if value is not None:
                ceiled = math.ceil(value * scale)
                if ceiled == value:
                    return ceiled + 1
                return ceiled
            case _:
                return None

    def _get_inclusive_discrete_max_bound(
        self, schema: dict[str, Any], scale: float
    ) -> int | None:
        # dummy variable because of pylint
        # see: <https://github.com/PyCQA/pylint/issues/5327>
        value = None
        match schema:
            case {"maximum": value} if value is not None:
                return math.floor(value * scale)
            case {"exclusiveMaximum": value} if value is not None:
                floored = math.floor(value * scale)
                if floored == value:
                    return floored - 1
                return floored
            case _:
                return None

    def _ex_integer(self, schema: dict[str, Any], *, scale: float = 1.0) -> int:
        inclusive_min = self._get_inclusive_discrete_min_bound(schema, scale)
        if inclusive_min is None:
            inclusive_min = round(-50 * scale)
        inclusive_max = self._get_inclusive_discrete_max_bound(schema, scale)
        if inclusive_max is None:
            inclusive_max = round(50 * scale)
        return self._rng.randint(inclusive_min, inclusive_max)

    def _ex_number(self, schema: dict[str, Any]) -> float:
        scale = 100.0
        return self._ex_integer(schema, scale=scale) / scale

    def _ex_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        example_obj: dict[str, Any] = {}
        try:
            required_keys: set[str] = set(schema["required"])
        except KeyError:
            required_keys = set()

        for prop_key, prop_schema in schema["properties"].items():
            if prop_key not in required_keys:
                if self._random_bool():
                    continue

            example_obj[prop_key] = self._ex_schema(prop_schema)
        return example_obj

    def _ex_array(self, schema: dict[str, Any]) -> list[Any]:
        example_array: list[Any] = []
        item_schema = schema["items"]
        length = self._rng.randrange(10)
        for _ in range(length):
            item = self._ex_schema(item_schema)
            example_array.append(item)
        return example_array

    def _ex_ref(self, ref: str) -> Any:
        _, _, name = ref.rpartition("/")
        definitions = self._root_schema["definitions"]
        schema = definitions[name]
        return self._ex_schema(schema)

    def _ex_schema(self, schema: dict[str, Any]) -> Any:
        match schema:
            case {"examples": examples}:
                return self._rng.choice(examples)
            case {"$ref": ref}:
                return self._ex_ref(ref)
            case {"enum": enum_values}:
                return self._rng.choice(enum_values)
            case {"oneOf": choices}:
                return self._ex_schema(self._rng.choice(choices))
            case {"type": "string"}:
                return self._ex_string(schema)
            case {"type": "boolean"}:
                return self._ex_boolean()
            case {"type": "integer"}:
                return self._ex_integer(schema)
            case {"type": "number"}:
                return self._ex_number(schema)
            case {"type": "object"}:
                return self._ex_object(schema)
            case {"type": "array"}:
                return self._ex_array(schema)
            case _:
                raise NotImplementedError(schema)

    def generate(self) -> Any:
        return self._ex_schema(self._root_schema)
