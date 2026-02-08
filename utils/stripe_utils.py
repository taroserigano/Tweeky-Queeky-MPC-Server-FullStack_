"""
Stripe payment utilities — create payment intents & verify payments.
"""
import stripe
from config.settings import settings

# Configure Stripe with the secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_stripe_payment_intent(amount_dollars: float, currency: str = "usd", metadata: dict = None) -> dict:
    """
    Create a Stripe PaymentIntent.

    Args:
        amount_dollars: Total in dollars (e.g. 129.99)
        currency: ISO currency code (default "usd")
        metadata: Optional dict (e.g. {"order_id": "abc123"})

    Returns:
        {"clientSecret": "pi_xxx_secret_xxx", "paymentIntentId": "pi_xxx"}
    """
    if not settings.STRIPE_SECRET_KEY:
        raise Exception("Stripe secret key not configured")

    # Stripe expects the amount in the smallest currency unit (cents for USD)
    amount_cents = int(round(amount_dollars * 100))

    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        automatic_payment_methods={"enabled": True},
        metadata=metadata or {},
    )

    return {
        "clientSecret": intent.client_secret,
        "paymentIntentId": intent.id,
    }


async def verify_stripe_payment(payment_intent_id: str) -> dict:
    """
    Retrieve a Stripe PaymentIntent and verify its status.

    Returns:
        {"verified": bool, "value": str}   (value is in dollars, stringified)
    """
    if not settings.STRIPE_SECRET_KEY:
        raise Exception("Stripe secret key not configured")

    intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    return {
        "verified": intent.status == "succeeded",
        "value": str(intent.amount / 100),  # convert cents → dollars string
    }
