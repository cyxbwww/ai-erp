from typing import Any


def api_success(data: Any = None, message: str = 'ok') -> dict[str, Any]:
    return {
        'code': 0,
        'message': message,
        'data': data
    }


def api_error(message: str = 'error', code: int = 1, data: Any = None) -> dict[str, Any]:
    return {
        'code': code,
        'message': message,
        'data': data
    }
