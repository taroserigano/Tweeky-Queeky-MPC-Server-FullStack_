import httpx
import base64
from config.settings import settings
from typing import Tuple, Dict


async def get_paypal_access_token() -> str:
    """Get PayPal access token"""
    # Check if credentials are placeholder values
    if settings.PAYPAL_CLIENT_ID == "your_paypal_client_id" or settings.PAYPAL_APP_SECRET == "your_paypal_secret":
        raise Exception("PayPal credentials not configured")
    
    auth = base64.b64encode(
        f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_APP_SECRET}".encode()
    ).decode()
    
    url = f"{settings.PAYPAL_API_URL}/v1/oauth2/token"
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Authorization": f"Basic {auth}",
    }
    
    data = {"grant_type": "client_credentials"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            raise Exception("Failed to get access token")
        
        paypal_data = response.json()
        return paypal_data["access_token"]


async def check_if_new_transaction(order_model, paypal_transaction_id: str) -> bool:
    """Check if the PayPal transaction ID has been used before"""
    try:
        orders = await order_model.find(
            {"payment_result.id": paypal_transaction_id}
        ).to_list()
        
        return len(orders) == 0
    except Exception:
        return False


async def verify_paypal_payment(paypal_transaction_id: str) -> Dict:
    """Verify PayPal payment"""
    access_token = await get_paypal_access_token()
    
    url = f"{settings.PAYPAL_API_URL}/v2/checkout/orders/{paypal_transaction_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception("Failed to verify payment")
        
        paypal_data = response.json()
        
        return {
            "verified": paypal_data["status"] == "COMPLETED",
            "value": paypal_data["purchase_units"][0]["amount"]["value"]
        }
