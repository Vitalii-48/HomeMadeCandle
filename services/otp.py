
import random
import time
from flask import session

def generate_otp(phone: str) -> str:
    code = str(random.randint(1000, 9999))
    session["otp"] = {
        "code": code,
        "phone": phone,
        "expires_at": time.time() + 300  # 5 хвилин
    }
    return code

def verify_otp(phone: str, code: str) -> bool:
    otp = session.get("otp")
    if not otp:
        return False
    if otp["phone"] != phone:
        return False
    if time.time() > otp["expires_at"]:
        return False
    if otp["code"] != code:
        return False
    session.pop("otp")
    session["phone_verified"] = phone
    return True