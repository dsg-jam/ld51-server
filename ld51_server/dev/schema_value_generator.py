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

    def _ex_boolean(self, schema: dict[str, Any]) -> bool:
        return self._random_bool()

    def _ex_integer(self) -> int:
        return self._rng.randrange(-500, 500)

    def _ex_number(self) -> float:
        return self._ex_integer() / 100.0

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
                return self._ex_boolean(schema)
            case {"type": "integer"}:
                return self._ex_integer()
            case {"type": "number"}:
                return self._ex_number()
            case {"type": "object"}:
                return self._ex_object(schema)
            case {"type": "array"}:
                return self._ex_array(schema)
            case _:
                raise NotImplementedError(schema)

    def generate(self) -> Any:
        return self._ex_schema(self._root_schema)
