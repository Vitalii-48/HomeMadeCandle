# services/nova_poshta/real.py
# Інтеграція з API Нової Пошти v2.
# Документація: https://developers.novaposhta.ua/
#
# Потрібна змінна середовища:
#   NOVA_POSHTA_API_KEY — API-ключ з особистого кабінету на novaposhta.ua

import requests
from flask import current_app

API_URL = "https://api.novaposhta.ua/v2.0/json/"
REQUEST_TIMEOUT = 5  # секунди


def _post(model: str, method: str, props: dict | None = None) -> list:
    """
    Виконує POST-запит до API Нової Пошти.

    Args:
        model:  назва моделі API (наприклад, "Address", "AddressGeneral").
        method: назва методу API (наприклад, "searchSettlements").
        props:  параметри запиту (methodProperties).

    Returns:
        list: масив data з відповіді або порожній список при помилці.
    """
    payload = {
        "apiKey":           current_app.config.get("NOVA_POSHTA_API_KEY", ""),
        "modelName":        model,
        "calledMethod":     method,
        "methodProperties": props or {},
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except requests.RequestException as e:
        current_app.logger.error("Нова Пошта API помилка (%s/%s): %s", model, method, e)
        return []


def search_cities(query: str) -> list:
    """
    Шукає населені пункти за назвою через API НП.

    Args:
        query: рядок пошуку (мінімум 2 символи рекомендовано).

    Returns:
        list: [{"ref": str, "name": str}, ...] — до 10 результатів.
    """
    raw = _post("Address", "searchSettlements", {
        "CityName": query,
        "Limit":    10,
    })
    addresses = raw[0].get("Addresses", []) if raw else []
    return [{"ref": a["DeliveryCity"], "name": a["Present"]} for a in addresses]


def get_warehouses(city_ref: str) -> list:
    """
    Повертає список відділень та поштоматів для вказаного міста.

    Args:
        city_ref: Ref міста (DeliveryCity) з результатів search_cities.

    Returns:
        list: [{"ref": str, "name": str}, ...] — до 50 відділень.
    """
    raw = _post("AddressGeneral", "getWarehouses", {
        "CityRef": city_ref,
        "Limit":   50,
    })
    return [{"ref": w["Ref"], "name": w["Description"]} for w in raw]