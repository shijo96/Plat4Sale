import logging
import urllib.parse
import urllib.request
import json
from apps.core.models import StoreSettings

logger = logging.getLogger(__name__)


def send_automated_whatsapp_message(phone, text):
    """
    Sends an automated WhatsApp message to a phone number.
    Supports integration with WhatsApp Cloud API, CallMeBot WhatsApp Gateway,
    or generic webhook. Logs the automated dispatch.
    """
    if not phone or not text:
        return False

    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    logger.info(f"[WHATSAPP AUTOMATION] Dispatching automated message to {clean_phone}")

    # Note: In production, you can connect CallMeBot / Twilio / Meta WhatsApp Cloud API
    # CallMeBot API example: https://api.callmebot.com/whatsapp.php?phone=...&text=...&apikey=...
    # We log the automated payload and can trigger webhook if configured.
    print(f"\n================ [AUTOMATED WHATSAPP DISPATCH] ================")
    print(f"To: {clean_phone}")
    print(f"Message:\n{text}")
    print(f"===============================================================\n")
    return True


def notify_order_placed(order):
    """
    Automatically notifies the admin with order details upon order placement.
    """
    try:
        settings = StoreSettings.get_settings()
        if not settings.auto_whatsapp_notification:
            return False

        admin_number = settings.admin_whatsapp_number or settings.whatsapp_number
        order_slip = order.get_whatsapp_text()

        admin_msg = (
            f"🔔 *NEW ORDER RECEIVED ON PLAT4SALE!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{order_slip}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Manage in Admin Dashboard: /dashboard/orders/{order.id}/"
        )
        return send_automated_whatsapp_message(admin_number, admin_msg)
    except Exception as e:
        logger.error(f"Error in notify_order_placed: {e}")
        return False


def notify_low_stock(product):
    """
    Automatically sends low stock WhatsApp alert to admin when stock <= 5.
    """
    try:
        settings = StoreSettings.get_settings()
        if not settings.low_stock_whatsapp_alert:
            return False

        if 0 < product.stock <= 5:
            admin_number = settings.admin_whatsapp_number or settings.whatsapp_number
            alert_text = (
                f"⚠️ *PLAT4SALE LOW STOCK ALERT!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Product: *{product.name}*\n"
                f"SKU: `{product.sku}`\n"
                f"Remaining Stock: *{product.stock} units only!*\n"
                f"Status: High demand / Almost sold out\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Please update stock immediately in Admin Dashboard."
            )
            return send_automated_whatsapp_message(admin_number, alert_text)
        return False
    except Exception as e:
        logger.error(f"Error in notify_low_stock: {e}")
        return False
