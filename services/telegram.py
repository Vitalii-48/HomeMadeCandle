# services/telegram.py
# Відправка повідомлень у Telegram-бот про нові замовлення.
#
# Налаштування (у .env або config.py):
#   TELEGRAM_BOT_TOKEN  — токен бота від @BotFather
#   TELEGRAM_CHAT_ID    — chat_id адміна або групи (можна отримати через @userinfobot)

import requests
from flask import current_app


def send_order_notification(order) -> None:
    """
    Відправляє повідомлення про нове замовлення у Telegram.
    Якщо токен або chat_id не налаштовані — мовчки пропускає.
    Якщо відправка не вдалась — логує помилку, але не кидає виняток,
    щоб не зламати оформлення замовлення.
    """
    token   = current_app.config.get("TELEGRAM_BOT_TOKEN")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        current_app.logger.warning("Telegram не налаштовано (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return

    text = _build_message(order)

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       text,
                "parse_mode": "HTML",  # дозволяє <b>, <i>, <code> у тексті
            },
            timeout=5,
        )
        if not resp.ok:
            current_app.logger.error(
                "Telegram sendMessage помилка: %s — %s", resp.status_code, resp.text
            )
    except requests.RequestException as e:
        current_app.logger.error("Telegram недоступний: %s", e)


def _build_message(order) -> str:
    """Формує текст повідомлення з деталями замовлення."""

    # ── Спосіб доставки ──
    if order.delivery_type == "nova_poshta":
        delivery = f"Нова Пошта\n  Місто: {order.np_city_name or '—'}\n  Відділення: {order.np_warehouse or '—'}"
    else:
        delivery = "Самовивіз"

    # ── Спосіб зв'язку ──
    contact_labels = {"phone": "Телефон", "viber": "Viber", "telegram": "Telegram"}
    contact = contact_labels.get(order.contact_method, order.contact_method)

    # ── Позиції замовлення ──
    lines = []
    for item in order.items:
        if item.product:
            name = item.product.name
            if item.color:
                name += f" ({item.color.color_name})"
        elif item.composition:
            name = item.composition.title
        else:
            name = "—"
        lines.append(f"  • {name} × {item.quantity} — {int(item.unit_price * item.quantity)} грн.")

    items_text = "\n".join(lines) if lines else "  (порожнє)"

    # ── Коментар ──
    comment_text = f"\n💬 <b>Коментар:</b> {order.comment}" if order.comment else ""

    return (
        f"🕯 <b>Нове замовлення #{order.order_number}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Ім'я:</b> {order.customer_name}\n"
        f"📞 <b>Телефон:</b> {order.phone}\n"
        f"📲 <b>Зв'язок:</b> {contact}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Доставка:</b> {delivery}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>Товари:</b>\n{items_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Сума:</b> {int(order.total_amount)} грн."
        f"{comment_text}"
    )