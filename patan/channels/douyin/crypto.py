"""Cryptographic signing utilities for Douyin API requests."""

from random import choice, randint, random
from re import compile, Match
from time import time
from typing import ClassVar
from urllib.parse import quote, urlencode

import httpx
from gmssl import func, sm3

from patan.channels.douyin.config import DouyinConfig
from patan.utils import generate_random_string, get_timestamp
from patan.utils.exceptions import APIResponseError
from patan.core.logging import logger


class ABogus:
    """A-Bogus signature generator for Douyin API requests."""

    __filter = compile(r"%([0-9A-F]{2})")
    __arguments = [0, 1, 14]
    __ua_key = "\u0000\u0001\u000e"
    __end_string = "cus"
    __version = [1, 0, 1, 5]
    __browser = "1536|742|1536|864|0|0|0|0|1536|864|1536|864|1536|742|24|24|MacIntel"
    __reg: ClassVar[list[int]] = [
        1937774191,
        1226093241,
        388252375,
        3666478592,
        2842636476,
        372324522,
        3817729613,
        2969243214,
    ]
    __str = {
        "s0": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
        "s1": "Dkdpgh4ZKsQB80/Mfvw36XI1R25+WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe=",
        "s2": "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe=",
        "s3": "ckdp1h4ZKsUB80/Mfvw36XIgR25+WQAlEi7NLboqYTOPuzmFjJnryx9HVGDaStCe",
        "s4": "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe",
    }

    def __init__(self, platform: str | None = None) -> None:
        self.chunk: list[int] = []
        self.size = 0
        self.reg = self.__reg[:]
        self.ua_code = [
            76, 98, 15, 131, 97, 245, 224, 133, 122, 199, 241, 166, 79, 34, 90, 191, 128, 126, 122, 98, 66, 11, 14,
            40, 49, 110, 110, 173, 67, 96, 138, 252,
        ]
        self.browser = self.generate_browser_info(platform) if platform else self.__browser
        self.browser_len = len(self.browser)
        self.browser_code = self.char_code_at(self.browser)

    @classmethod
    def list_1(cls, random_num: float | None = None, a: int = 170, b: int = 85, c: int = 45) -> list[int]:
        return cls.random_list(random_num, a, b, 1, 2, 5, c & a)

    @classmethod
    def list_2(cls, random_num: float | None = None, a: int = 170, b: int = 85) -> list[int]:
        return cls.random_list(random_num, a, b, 1, 0, 0, 0)

    @classmethod
    def list_3(cls, random_num: float | None = None, a: int = 170, b: int = 85) -> list[int]:
        return cls.random_list(random_num, a, b, 1, 0, 5, 0)

    @staticmethod
    def random_list(a: float | None = None, b: int = 170, c: int = 85, d: int = 0, e: int = 0, f: int = 0,
                    g: int = 0) -> list[int]:
        r = a or (random() * 10000)
        v = [r, int(r) & 255, int(r) >> 8]
        s = v[1] & b | d
        v.append(s)
        s = v[1] & c | e
        v.append(s)
        s = v[2] & b | f
        v.append(s)
        s = v[2] & c | g
        v.append(s)
        return v[-4:]

    @staticmethod
    def from_char_code(*args: int) -> str:
        return "".join(chr(code) for code in args)

    @classmethod
    def generate_string_1(cls, random_num_1: float | None = None, random_num_2: float | None = None,
                          random_num_3: float | None = None) -> str:
        return (cls.from_char_code(*cls.list_1(random_num_1)) +
                cls.from_char_code(*cls.list_2(random_num_2)) +
                cls.from_char_code(*cls.list_3(random_num_3)))

    def generate_string_2(self, url_params: str, method: str = "GET", start_time: int = 0,
                          end_time: int = 0) -> str:
        a = self.generate_string_2_list(url_params, method, start_time, end_time)
        e = self.end_check_num(a)
        a.extend(self.browser_code)
        a.append(e)
        return self.rc4_encrypt(self.from_char_code(*a), "y")

    def generate_string_2_list(self, url_params: str, method: str = "GET", start_time: int = 0,
                               end_time: int = 0) -> list[int]:
        start_time = start_time or int(time() * 1000)
        end_time = end_time or (start_time + randint(4, 8))
        params_array = self.generate_params_code(url_params)
        method_array = self.generate_method_code(method)
        return self.list_4(
            (end_time >> 24) & 255,
            params_array[21],
            self.ua_code[23],
            (end_time >> 16) & 255,
            params_array[22],
            self.ua_code[24],
            (end_time >> 8) & 255,
            (end_time >> 0) & 255,
            (start_time >> 24) & 255,
            (start_time >> 16) & 255,
            (start_time >> 8) & 255,
            (start_time >> 0) & 255,
            method_array[21],
            method_array[22],
            int(end_time / 256 / 256 / 256 / 256) >> 0,
            int(start_time / 256 / 256 / 256 / 256) >> 0,
            self.browser_len,
        )

    @staticmethod
    def reg_to_array(a: list[int]) -> list[int]:
        o = [0] * 32
        for i in range(8):
            c = a[i]
            o[4 * i + 3] = 255 & c
            c >>= 8
            o[4 * i + 2] = 255 & c
            c >>= 8
            o[4 * i + 1] = 255 & c
            c >>= 8
            o[4 * i] = 255 & c
        return o

    def compress(self, a: list[int]) -> None:
        f = self.generate_f(a)
        i = self.reg[:]
        for o in range(64):
            c = self.de(i[0], 12) + i[4] + self.de(self.pe(o), o)
            c = c & 0xFFFFFFFF
            c = self.de(c, 7)
            s = (c ^ self.de(i[0], 12)) & 0xFFFFFFFF
            u = self.he(o, i[0], i[1], i[2])
            u = (u + i[3] + s + f[o + 68]) & 0xFFFFFFFF
            b = self.ve(o, i[4], i[5], i[6])
            b = (b + i[7] + c + f[o]) & 0xFFFFFFFF
            i[3] = i[2]
            i[2] = self.de(i[1], 9)
            i[1] = i[0]
            i[0] = u
            i[7] = i[6]
            i[6] = self.de(i[5], 19)
            i[5] = i[4]
            i[4] = (b ^ self.de(b, 9) ^ self.de(b, 17)) & 0xFFFFFFFF
        for idx in range(8):
            self.reg[idx] = (self.reg[idx] ^ i[idx]) & 0xFFFFFFFF

    @classmethod
    def generate_f(cls, e: list[int]) -> list[int]:
        r = [0] * 132
        for t in range(16):
            r[t] = (e[4 * t] << 24) | (e[4 * t + 1] << 16) | (e[4 * t + 2] << 8) | e[4 * t + 3]
            r[t] &= 0xFFFFFFFF
        for n in range(16, 68):
            a = r[n - 16] ^ r[n - 9] ^ cls.de(r[n - 3], 15)
            a = a ^ cls.de(a, 15) ^ cls.de(a, 23)
            r[n] = (a ^ cls.de(r[n - 13], 7) ^ r[n - 6]) & 0xFFFFFFFF
        for n in range(68, 132):
            r[n] = (r[n - 68] ^ r[n - 64]) & 0xFFFFFFFF
        return r

    @staticmethod
    def pad_array(arr: list[int], length: int = 60) -> list[int]:
        while len(arr) < length:
            arr.append(0)
        return arr

    def fill(self, length: int = 60) -> None:
        size = 8 * self.size
        self.chunk.append(128)
        self.chunk = self.pad_array(self.chunk, length)
        for i in range(4):
            self.chunk.append((size >> 8 * (3 - i)) & 255)

    @staticmethod
    def list_4(a: int, b: int, c: int, d: int, e: int, f: int, g: int, h: int, i: int, j: int, k: int,
               m: int, n: int, o: int, p: int, q: int, r: int) -> list[int]:
        return [44, a, 0, 0, 0, 0, 24, b, n, 0, c, d, 0, 0, 0, 1, 0, 239, e, o, f, g, 0, 0, 0, 0, h, 0, 0, 14,
                i, j, 0, k, m, 3, p, 1, q, 1, r, 0, 0, 0]

    @staticmethod
    def end_check_num(a: list[int]) -> int:
        r = 0
        for i in a:
            r ^= i
        return r

    @classmethod
    def decode_string(cls, url_string: str) -> str:
        decoded = cls.__filter.sub(cls.replace_func, url_string)
        return decoded

    @staticmethod
    def replace_func(match: Match[str]) -> str:
        return chr(int(match.group(1), 16))

    @staticmethod
    def de(e: int, r: int) -> int:
        r %= 32
        return ((e << r) & 0xFFFFFFFF) | (e >> (32 - r))

    @staticmethod
    def pe(e: int) -> int:
        return 2043430169 if 0 <= e < 16 else 2055708042

    @staticmethod
    def he(e: int, r: int, t: int, n: int) -> int:
        if 0 <= e < 16:
            return (r ^ t ^ n) & 0xFFFFFFFF
        elif 16 <= e < 64:
            return (r & t | r & n | t & n) & 0xFFFFFFFF
        raise ValueError

    @staticmethod
    def ve(e: int, r: int, t: int, n: int) -> int:
        if 0 <= e < 16:
            return (r ^ t ^ n) & 0xFFFFFFFF
        elif 16 <= e < 64:
            return (r & t | ~r & n) & 0xFFFFFFFF
        raise ValueError

    @staticmethod
    def convert_to_char_code(a: str) -> list[int]:
        return [ord(i) for i in a]

    @staticmethod
    def split_array(arr: list[int], chunk_size: int = 64) -> list[list[int]]:
        return [arr[i: i + chunk_size] for i in range(0, len(arr), chunk_size)]

    @staticmethod
    def char_code_at(s: str) -> list[int]:
        return [ord(char) for char in s]

    def write(self, e: str | list[int]) -> None:
        self.size = len(e)
        if isinstance(e, str):
            e = self.decode_string(e)
            e = self.char_code_at(e)
        if len(e) <= 64:
            self.chunk = e
        else:
            chunks = self.split_array(e, 64)
            for i in chunks[:-1]:
                self.compress(i)
            self.chunk = chunks[-1]

    def reset(self) -> None:
        self.chunk = []
        self.size = 0
        self.reg = self.__reg[:]

    def sum(self, e: str | list[int], length: int = 60) -> list[int]:
        self.reset()
        self.write(e)
        self.fill(length)
        self.compress(self.chunk)
        return self.reg_to_array(self.reg)

    @classmethod
    def generate_result_unit(cls, n: int, s: str) -> str:
        r = ""
        for i, j in zip(range(18, -1, -6), (16515072, 258048, 4032, 63)):
            r += cls.__str[s][(n & j) >> i]
        return r

    @classmethod
    def generate_result_end(cls, s: str, e: str = "s4") -> str:
        r = ""
        b = ord(s[120]) << 16
        r += cls.__str[e][(b & 16515072) >> 18]
        r += cls.__str[e][(b & 258048) >> 12]
        r += "=="
        return r

    @classmethod
    def generate_result(cls, s: str, e: str = "s4") -> str:
        r = []
        for i in range(0, len(s), 3):
            if i + 2 < len(s):
                n = (ord(s[i]) << 16) | (ord(s[i + 1]) << 8) | ord(s[i + 2])
            elif i + 1 < len(s):
                n = (ord(s[i]) << 16) | (ord(s[i + 1]) << 8)
            else:
                n = ord(s[i]) << 16
            for j, k in zip(range(18, -1, -6), (0xFC0000, 0x03F000, 0x0FC0, 0x3F)):
                if j == 6 and i + 1 >= len(s):
                    break
                if j == 0 and i + 2 >= len(s):
                    break
                r.append(cls.__str[e][(n & k) >> j])
        r.append("=" * ((4 - len(r) % 4) % 4))
        return "".join(r)

    @classmethod
    def generate_args_code(cls) -> list[int]:
        a = []
        for j in range(24, -1, -8):
            a.append(cls.__arguments[0] >> j)
        a.append(cls.__arguments[1] / 256)
        a.append(cls.__arguments[1] % 256)
        a.append(cls.__arguments[1] >> 24)
        a.append(cls.__arguments[1] >> 16)
        for j in range(24, -1, -8):
            a.append(cls.__arguments[2] >> j)
        return [int(i) & 255 for i in a]

    def generate_method_code(self, method: str = "GET") -> list[int]:
        return self.sm3_to_array(self.sm3_to_array(method + self.__end_string))

    def generate_params_code(self, params: str) -> list[int]:
        return self.sm3_to_array(self.sm3_to_array(params + self.__end_string))

    @classmethod
    def sm3_to_array(cls, data: str | list[int]) -> list[int]:
        """Calculate SM3 hash and convert to integer array."""
        if isinstance(data, str):
            b = data.encode("utf-8")
        else:
            b = bytes(data)
        h = sm3.sm3_hash(func.bytes_to_list(b))
        return [int(h[i: i + 2], 16) for i in range(0, len(h), 2)]

    @classmethod
    def generate_browser_info(cls, platform: str = "Win32") -> str:
        inner_width = randint(1280, 1920)
        inner_height = randint(720, 1080)
        outer_width = randint(inner_width, 1920)
        outer_height = randint(inner_height, 1080)
        value_list = [
            inner_width, inner_height, outer_width, outer_height,
            0, choice((0, 30)), 0, 0,
            outer_width, outer_height, outer_width, outer_height,
            inner_width, inner_height, 24, 24, platform,
        ]
        return "|".join(str(i) for i in value_list)

    @staticmethod
    def rc4_encrypt(plaintext: str, key: str) -> str:
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + ord(key[i % len(key)])) % 256
            s[i], s[j] = s[j], s[i]
        i = 0
        j = 0
        cipher = []
        for k in range(len(plaintext)):
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            t = (s[i] + s[j]) % 256
            cipher.append(chr(s[t] ^ ord(plaintext[k])))
        return "".join(cipher)

    def get_value(self, url_params: str | dict[str, str], method: str = "GET", start_time: int = 0,
                  end_time: int = 0, random_num_1: float | None = None, random_num_2: float | None = None,
                  random_num_3: float | None = None) -> str:
        string_1 = self.generate_string_1(random_num_1, random_num_2, random_num_3)
        string_2 = self.generate_string_2(
            urlencode(url_params) if isinstance(url_params, dict) else url_params,
            method, start_time, end_time,
        )
        string = string_1 + string_2
        return self.generate_result(string, "s4")


class XBogus:
    """X-Bogus signature generator for Douyin API requests."""

    def __init__(self, user_agent: str | None = None) -> None:
        # fmt: off
        self.Array: list[int | None] = [
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, 10, 11, 12, 13, 14, 15
        ]
        self.character = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
        # fmt: on
        self.ua_key = b"\x00\x01\x0c"
        self.user_agent = (
            user_agent
            if user_agent
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        )

    def md5_str_to_array(self, md5_str: str) -> list[int]:
        if isinstance(md5_str, str) and len(md5_str) > 32:
            return [ord(char) for char in md5_str]
        array = []
        idx = 0
        while idx < len(md5_str):
            high = self.Array[ord(md5_str[idx])]  # type: ignore[index]
            low = self.Array[ord(md5_str[idx + 1])]  # type: ignore[index]
            if high is not None and low is not None:
                array.append((high << 4) | low)
            idx += 2
        return array

    def md5_encrypt(self, url_path: str) -> list[int]:
        hashed_url_path = self.md5_str_to_array(self.md5(self.md5_str_to_array(self.md5(url_path))))
        return hashed_url_path

    def md5(self, input_data: str | list[int]) -> str:
        if isinstance(input_data, str):
            array = self.md5_str_to_array(input_data)
        elif isinstance(input_data, list):
            array = input_data
        else:
            raise ValueError("Invalid input type. Expected str or list.")

        # Ensure all values are in valid byte range
        cleaned_array = [x & 0xFF for x in array if isinstance(x, int)]

        import hashlib
        md5_hash = hashlib.md5()
        md5_hash.update(bytes(cleaned_array))
        return md5_hash.hexdigest()

    def encoding_conversion(self, a: int, b: int, c: int, e: int, d: int, t: int, f: int, r: int,
                           n: int, o: int, i: int, _: int, x: int, u: int, s: int, idx: int, v: int,
                           h: int, p: int) -> str:
        y = [a]
        y.append(int(i))
        y.extend([b, _, c, x, e, u, d, s, t, idx, f, v, r, h, n, p, o])
        return bytes(y).decode("ISO-8859-1")

    @staticmethod
    def encoding_conversion2(a: int, b: int, c: str) -> str:
        return chr(a) + chr(b) + c

    @staticmethod
    def rc4_encrypt(key: bytes, data: bytes) -> bytearray:
        s = list(range(256))
        j = 0
        encrypted_data = bytearray()
        for i in range(256):
            j = (j + s[i] + key[i % len(key)]) % 256
            s[i], s[j] = s[j], s[i]
        i = j = 0
        for byte in data:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            encrypted_byte = byte ^ s[(s[i] + s[j]) % 256]
            encrypted_data.append(encrypted_byte)
        return encrypted_data

    @staticmethod
    def calculation(a1: int, a2: int, a3: int) -> str:
        x1 = (a1 & 255) << 16
        x2 = (a2 & 255) << 8
        x3 = x1 | x2 | a3
        return (
            "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="[(x3 & 16515072) >> 18]
            + "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="[(x3 & 258048) >> 12]
            + "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="[(x3 & 4032) >> 6]
            + "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="[x3 & 63]
        )

    def getXBogus(self, url_path: str) -> tuple[str, str, str]:
        array1 = self.md5_str_to_array(
            self.md5(
                __import__("base64").b64encode(self.rc4_encrypt(self.ua_key, self.user_agent.encode("ISO-8859-1"))).decode(
                    "ISO-8859-1")
            )
        )
        array2 = self.md5_str_to_array(self.md5(self.md5_str_to_array("d41d8cd98f00b204e9800998ecf8427e")))
        url_path_array = self.md5_encrypt(url_path)
        timer = int(time())
        ct = 536919696
        array3: list[int] = []
        array4: list[int] = []
        xb_ = ""
        # fmt: off
        new_array = [
            64, 0.00390625, 1, 12,
            url_path_array[14], url_path_array[15], array2[14], array2[15], array1[14], array1[15],
            timer >> 24 & 255, timer >> 16 & 255, timer >> 8 & 255, timer & 255,
            ct >> 24 & 255, ct >> 16 & 255, ct >> 8 & 255, ct & 255
        ]
        # fmt: on
        xor_result = int(new_array[0])
        for i in range(1, len(new_array)):
            b = new_array[i]
            if isinstance(b, float):
                b = int(b)
            xor_result ^= b
        new_array.append(xor_result)
        idx = 0
        while idx < len(new_array):
            array3.append(new_array[idx])
            try:
                array4.append(new_array[idx + 1])
            except IndexError:
                pass
            idx += 2
        merge_array = array3 + array4
        garbled_code = self.encoding_conversion2(
            2,
            255,
            self.rc4_encrypt(
                "ÿ".encode("ISO-8859-1"),
                self.encoding_conversion(*merge_array).encode("ISO-8859-1"),
            ).decode("ISO-8859-1"),
        )
        idx = 0
        while idx < len(garbled_code):
            xb_ += self.calculation(
                ord(garbled_code[idx]),
                ord(garbled_code[idx + 1]),
                ord(garbled_code[idx + 2]),
            )
            idx += 3
        self.params = f"{url_path}&X-Bogus={xb_}"
        self.xb = xb_
        return (self.params, self.xb, self.user_agent)


def generate_verify_fp() -> str:
    """Generate a verify_fp fingerprint identifier."""
    base_str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    milliseconds = int(round(time() * 1000))
    base36 = ""
    while milliseconds > 0:
        remainder = milliseconds % 36
        base36 = (str(remainder) if remainder < 10 else chr(ord("a") + remainder - 10)) + base36
        milliseconds //= 36
    chars: list[str] = [""] * 36
    chars[8] = chars[13] = chars[18] = chars[23] = "_"
    chars[14] = "4"
    for index in range(36):
        if chars[index]:
            continue
        value = int(random() * len(base_str))
        if index == 19:
            value = 3 & value | 8
        chars[index] = base_str[value]
    return "verify_" + base36 + "_" + "".join(chars)


def generate_web_id() -> str:
    """Generate a web_id identifier (alias for verify_fp)."""
    return generate_verify_fp()


def sign_url_with_xbogus(endpoint: str, user_agent: str) -> str:
    """Sign a URL with X-Bogus parameter."""
    try:
        return XBogus(user_agent).getXBogus(endpoint)[0]
    except Exception as exc:
        raise RuntimeError(f"failed to generate X-Bogus: {exc}") from exc


def build_xbogus_signed_url(base_endpoint: str, params: dict[str, str], user_agent: str) -> str:
    """Build a URL with X-Bogus signature."""
    param_str = "&".join(f"{key}={value}" for key, value in params.items())
    try:
        xbogus_value = XBogus(user_agent).getXBogus(param_str)[1]
    except Exception as exc:
        raise RuntimeError(f"failed to generate X-Bogus: {exc}") from exc
    separator = "&" if "?" in base_endpoint else "?"
    return f"{base_endpoint}{separator}{param_str}&X-Bogus={xbogus_value}"


def build_abogus_value(params: dict[str, str], user_agent: str) -> str:
    """Build A-Bogus signature value."""
    try:
        return quote(ABogus().get_value(dict(params)), safe="")
    except Exception as exc:
        raise RuntimeError(f"failed to generate A-Bogus: {exc}") from exc


def generate_ms_token(config: DouyinConfig | None = None) -> str:
    """Generate msToken from Douyin API."""
    import json

    active_config = config or DouyinConfig.load()
    payload = json.dumps({
        "magic": active_config.ms_token_conf["magic"],
        "version": active_config.ms_token_conf["version"],
        "dataType": active_config.ms_token_conf["dataType"],
        "strData": active_config.ms_token_conf["strData"],
        "tspFromClient": get_timestamp(),
    })
    headers = {
        "User-Agent": active_config.ms_token_conf["User-Agent"],
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(proxy=active_config.proxies.get("https://"),
                          transport=httpx.HTTPTransport(retries=5)) as client:
            response = client.post(active_config.ms_token_conf["url"], content=payload, headers=headers)
            response.raise_for_status()
            ms_token = str(httpx.Cookies(response.cookies).get("msToken"))
            if len(ms_token) not in {120, 128}:
                raise APIResponseError("msToken length is invalid")
            return ms_token
    except Exception as exc:
        logger.warning("failed to fetch msToken, falling back to generated token: %s", exc)
        return generate_fake_ms_token()


def generate_fake_ms_token() -> str:
    """Generate a fake msToken for fallback."""
    return generate_random_string(126) + "=="


def generate_ttwid(config: DouyinConfig) -> str:
    """Generate ttwid token from Douyin API."""
    with httpx.Client(transport=httpx.HTTPTransport(retries=5)) as client:
        response = client.post(config.ttwid_conf["url"], content=config.ttwid_conf["data"])
        response.raise_for_status()
        return str(httpx.Cookies(response.cookies).get("ttwid"))
