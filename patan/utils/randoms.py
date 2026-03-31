import random
import secrets

random.seed(int.from_bytes(secrets.token_bytes(16), "big"))


def generate_random_string(length: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
    return "".join(random.choice(alphabet) for _ in range(length))
