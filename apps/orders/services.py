import hmac
import hashlib
import base64
SECRET='1383b8c99cd60a619305a73c998a7707819d69272b1e5b6933c854e6f3e52137'


def verify_webhook(data, hmac_header):
    """
    Verify that the data is from Shopify
    """
    digest = hmac.new(SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))


def shopify_order(data):
    """
    Format the order data to be sent to the client
    """
    return_data = {
        "order_id": str(data["id"]),
        "order": {
            "created_at": data["created_at"],
            "total_price": data["total_price"],
            "total_weight": data["total_weight"],
            "currency": data["currency"],
            "financial_status": data["financial_status"],
            "order_number": data["order_number"],
            "order_status_url": data["order_status_url"],
            "line_items": data["line_items"],
        }
    }
    if data.get("billing_address"):
        return_data["order"]["billing_address"] = {
                "city": data["billing_address"]["city"],
                "country": data["billing_address"]["country"],
                "country_code": data["billing_address"]["country_code"],
        }
    if data.get("shipping_address"):
        return_data["order"]["shipping_address"] = {
                "city": data["shipping_address"]["city"],
                "country": data["shipping_address"]["country"],
                "country_code": data["shipping_address"]["country_code"],
        }

    return return_data