import base64
import uuid
import requests
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

# ============================================================
# КОНФИГУРАЦИЯ API
# ============================================================

API_URL = "https://api.yookassa.ru/v3"

def _get_auth_header() -> str:
    """
    Создаёт заголовок Authorization для Basic Auth.
    
    ЮKassa ожидает: 'Basic ' + base64(shopId:secretKey)
    """
    credentials = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
    # Кодируем в байты, потом в base64, потом обратно в строку
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded}"

def _get_idempotence_key() -> str:
    """
    Генерирует ключ идемпотентности.
    
    Если запрос не дошёл из-за проблем с сетью, и ты повторил его 
    с тем же ключом - ЮKassa не создаст дубликат платежа, а вернёт 
    результат первого запроса.
    """
    return str(uuid.uuid4())


# ============================================================
# СОЗДАНИЕ ПЛАТЕЖА
# ============================================================

def create_payment(amount: float, description: str, user_id: int) -> tuple[str, str]:
    """
    Создаёт платёж через POST /v3/payments
    
    Возвращает: (payment_id, confirmation_url)
    """
    
    # 1. Готовим URL
    url = f"{API_URL}/payments"
    
    # 2. Готовим заголовки
    headers = {
        "Authorization": _get_auth_header(),
        "Idempotence-Key": _get_idempotence_key(),
        "Content-Type": "application/json"
    }
    
    # 3. Готовим тело запроса
    body = {
        "amount": {
            "value": f"{amount:.2f}",  # ЮKassa ждёт строку "100.00"
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot_username"  # Куда вернуть после оплаты
        },
        "description": description,
        "metadata": {
            "user_id": user_id  # Наши данные для идентификации
        },
        "capture": True  # Списать деньги сразу
    }
    
    # 4. Отправляем POST-запрос
    response = requests.post(url, headers=headers, json=body)
    
    # 5. Проверяем, всё ли хорошо
    if response.status_code == 200:
        data = response.json()
        payment_id = data["id"]
        confirmation_url = data["confirmation"]["confirmation_url"]
        return payment_id, confirmation_url
    else:
        # Если что-то пошло не так - показываем ошибку
        raise Exception(f"Ошибка создания платежа: {response.status_code} - {response.text}")


# ============================================================
# ПРОВЕРКА СТАТУСА ПЛАТЕЖА
# ============================================================

def check_payment(payment_id: str) -> str:
    """
    Проверяет статус платежа через GET /v3/payments/{payment_id}
    
    Возможные статусы:
    - 'pending'           - платёж создан, но не оплачен
    - 'waiting_for_capture' - деньги заблокированы (для двухстадийной оплаты)
    - 'succeeded'         - оплачен успешно
    - 'canceled'          - отменён
    """
    
    # 1. Готовим URL
    url = f"{API_URL}/payments/{payment_id}"
    
    # 2. Готовим заголовки
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json"
    }
    
    # 3. Отправляем GET-запрос
    response = requests.get(url, headers=headers)
    
    # 4. Обрабатываем ответ
    if response.status_code == 200:
        data = response.json()
        return data["status"]
    else:
        raise Exception(f"Ошибка проверки платежа: {response.status_code} - {response.text}")


# ============================================================
# ДОПОЛНИТЕЛЬНО: ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПЛАТЕЖЕ
# ============================================================

def get_payment_info(payment_id: str) -> dict:
    """
    Получает полную информацию о платеже.
    Полезно для отладки и логов.
    """
    url = f"{API_URL}/payments/{payment_id}"
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Ошибка получения информации: {response.status_code}")