def getResponseBody(status: bool = True, data: dict = {}, errorCode: int = 0, errorMessage: str = '') -> dict:
    """Функция для стандартизации ответов пользователю"""

    return {
        'status': status,
        'data': data,
        'errorCode': errorCode,
        'errorMessage': errorMessage
    }


def setResponseCookie(response, name: str, data: str = '', expires: str = 'Tue, 19 Jan 2038 03:14:07 GMT'):
    """Функция для установки бесконечных кук"""
    response.set_cookie(name, data, expires=expires, secure=True, samesite='none')


def deleteCookieFromResponse(response, name: str):
    """Функция для удаления кук"""
    response.delete_cookie(name, httponly=False, samesite='none', secure=True)
