import random
import string

# alphanumerics but without characters that are easily confused
_ALPHABET: list[str] = sorted(set(string.ascii_uppercase + string.digits) - set("OI01"))


class JoinCodeGenerator:
    _alphabet: list[str]
    _alphabet_base: int

    _min_len: int
    _len: int
    _last_value: int

    def __init__(self, *, min_len: int = 3, shuffle_alphabet: bool = True) -> None:
        self._alphabet = _ALPHABET.copy()
        self._alphabet_base = len(self._alphabet)
        if shuffle_alphabet:
            random.shuffle(self._alphabet)

        self._min_len = max(min_len, 1)
        self.reset_len()

    def _encode(self, val: int) -> str:
        encoded = ""
        # feed in the previous digit as an offset to make the pattern appear more random
        last_digit = 0

        while val > 0:
            val, digit = divmod(val, self._alphabet_base)
            actual_digit = (digit + last_digit) % self._alphabet_base
            encoded += self._alphabet[actual_digit]
            last_digit = actual_digit + 1

        return encoded

    def _set_len(self, length: int) -> None:
        self._len = length
        # set the value to the first numeric value with 'len' digits
        self._last_value = self._alphabet_base ** (self._len - 1)

    def reset_len(self) -> None:
        self._set_len(self._min_len)

    def bump_len(self) -> None:
        self._set_len(self._len + 1)

    def generate(self) -> str:
        self._last_value = (self._last_value + 1) % (self._alphabet_base**self._len)
        return self._encode(self._last_value)
