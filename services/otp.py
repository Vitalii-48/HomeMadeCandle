# services/otp.py
# Генерація та верифікація одноразових кодів підтвердження телефону (OTP).
# Код зберігається у Flask-сесії — серверна БД не потрібна.
# Термін дії: 5 хвилин.

import random
import time
from flask import session

OTP_TTL = 300       # термін дії коду в секундах (5 хвилин)
OTP_DIGITS = 4      # кількість цифр у коді


def generate_otp(phone: str) -> str:
    """
    Генерує 4-значний OTP-код та зберігає його у сесії.

    Кожен новий виклик перезаписує попередній код для цього телефону.
    У продакшені код треба надсилати через SMS-сервіс (Twilio, Turbosms тощо).

    Args:
        phone: номер телефону у будь-якому форматі (зберігається як є).

    Returns:
        str: згенерований код (для dev-режиму повертається у відповіді API).
    """
    code = str(random.randint(10 ** (OTP_DIGITS - 1), 10 ** OTP_DIGITS - 1))
    session["otp"] = {
        "code": code,
        "phone": phone,
        "expires_at": time.time() + OTP_TTL,
    }
    return code


def verify_otp(phone: str, code: str) -> bool:
    """
    Перевіряє OTP-код для вказаного телефону.

    Валідація провалюється якщо:
    - OTP відсутній у сесії;
    - телефон не збігається;
    - код прострочений;
    - код невірний.

    У разі успіху — видаляє OTP із сесії (одноразове використання)
    та зберігає верифікований телефон у session["phone_verified"].

    Args:
        phone: номер телефону, що верифікується.
        code: код, введений користувачем.

    Returns:
        bool: True якщо код правильний і актуальний, False — інакше.
    """
    otp = session.get("otp")

    if not otp:
        return False
    if otp["phone"] != phone:
        return False
    if time.time() > otp["expires_at"]:
        session.pop("otp", None)  # очищаємо прострочений код
        return False
    if otp["code"] != code:
        return False

    # Код вірний — очищаємо та фіксуємо верифікований номер
    session.pop("otp", None)
    session["phone_verified"] = phone
    return True