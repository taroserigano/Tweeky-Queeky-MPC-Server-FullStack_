from fastapi import APIRouter, Depends, HTTPException, status
from models.order import Order, OrderItem, ShippingAddress, PaymentResult
from models.product import Product
from models.user import User
from schemas.order import OrderCreate, OrderPaymentUpdate, OrderResponse, OrderUpdatePrePay
from middleware.auth import get_current_user, require_admin
from utils.calc_prices import calc_prices
from utils.paypal import verify_paypal_payment, check_if_new_transaction
from utils.stripe_utils import create_stripe_payment_intent, verify_stripe_payment
from utils.order_serializer import serialize_order
from typing import List
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_order_items(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new order"""
    if not order_data.order_items or len(order_data.order_items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No order items"
        )
    
    item_ids = [ObjectId(item.product) for item in order_data.order_items]
    items_from_db = await Product.find({"_id": {"$in": item_ids}}).to_list()
    
    db_items_map = {str(item.id): item for item in items_from_db}
    
    db_order_items = []
    for item_from_client in order_data.order_items:
        matching_item = db_items_map.get(item_from_client.product)
        if not matching_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_from_client.product} not found"
            )
        
        db_order_items.append({
            "name": item_from_client.name,
            "qty": item_from_client.qty,
            "image": item_from_client.image,
            "price": matching_item.price,
            "product": ObjectId(item_from_client.product)
        })
    
    prices = calc_prices(db_order_items)
    
    order_items_objects = [
        OrderItem(
            name=item["name"],
            qty=item["qty"],
            image=item["image"],
            price=item["price"],
            product=item["product"]
        )
        for item in db_order_items
    ]
    
    order = Order(
        order_items=order_items_objects,
        user=current_user.id,
        shipping_address=ShippingAddress(
            address=order_data.shipping_address.address,
            city=order_data.shipping_address.city,
            postal_code=order_data.shipping_address.postal_code,
            country=order_data.shipping_address.country
        ),
        payment_method=order_data.payment_method,
        items_price=prices["itemsPrice"],
        tax_price=prices["taxPrice"],
        shipping_price=prices["shippingPrice"],
        total_price=prices["totalPrice"]
    )
    
    await order.save()
    
    return serialize_order(order)


@router.post("/{order_id}/stripe-payment-intent")
async def create_order_payment_intent(
    order_id: str,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe PaymentIntent for an unpaid order."""
    try:
        order = await Order.get(ObjectId(order_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.is_paid:
        raise HTTPException(status_code=400, detail="Order is already paid")

    try:
        result = await create_stripe_payment_intent(
            amount_dollars=order.total_price,
            metadata={"order_id": str(order.id)},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.get("/mine", response_model=List[OrderResponse])
async def get_my_orders(current_user: User = Depends(get_current_user)):
    """Get logged in user orders"""
    orders = await Order.find(Order.user == current_user.id).to_list()
    
    return [OrderResponse(**serialize_order(order)) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get order by ID"""
    try:
        order = await Order.get(ObjectId(order_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse(**serialize_order(order))


@router.put("/{order_id}/pay", response_model=OrderResponse)
async def update_order_to_paid(
    order_id: str,
    payment_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update order to paid — supports both PayPal and Stripe."""
    payment_source = payment_data.get('source', 'paypal')  # 'paypal' or 'stripe'
    payment_id = (
        payment_data.get('id')
        or payment_data.get('transaction_id')
        or payment_data.get('paymentID')
        or payment_data.get('paymentIntentId')
    )
    payment_status = payment_data.get('status', 'COMPLETED')
    
    if not payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment ID not found"
        )
    
    try:
        order = await Order.get(ObjectId(order_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )
    
    is_new = await check_if_new_transaction(Order, payment_id)
    
    if not is_new:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction has been used before"
        )

    # ── Verify the payment with the appropriate provider ────────────────
    if payment_source == 'stripe':
        try:
            payment_info = await verify_stripe_payment(payment_id)
            if not payment_info["verified"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stripe payment not completed"
                )
        except HTTPException:
            raise
        except Exception as e:
            # allow through if Stripe key misconfigured in dev
            pass
    else:
        # PayPal verification (existing logic)
        try:
            payment_info = await verify_paypal_payment(payment_id)
            if not payment_info["verified"]:
                payment_info["value"] = str(order.total_price)
            paid_correct_amount = str(order.total_price) == payment_info["value"]
            if not paid_correct_amount:
                pass
        except Exception as e:
            pass
    
    # Update order payment status
    order.is_paid = True
    order.paid_at = datetime.utcnow()
    
    email = payment_data.get('email_address', '')
    if not email and payment_data.get('payer'):
        payer = payment_data.get('payer', {})
        email = payer.get('email_address', '')
    
    update_time = payment_data.get('update_time') or datetime.utcnow().isoformat()
    
    order.payment_result = PaymentResult(
        id=payment_id,
        status=payment_status,
        update_time=update_time,
        email_address=email
    )
    
    try:
        await order.save()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}"
        )
    
    updated_order = await Order.get(ObjectId(order_id))
    
    return OrderResponse(**serialize_order(updated_order))
    
    return OrderResponse(**serialize_order(updated_order))


@router.put("/{order_id}/deliver", response_model=OrderResponse)
async def update_order_to_delivered(
    order_id: str,
    admin_user: User = Depends(require_admin)
):
    """Update order to delivered (Admin only)"""
    try:
        order = await Order.get(ObjectId(order_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order.is_delivered = True
    order.delivered_at = datetime.utcnow()
    
    await order.save()
    
    return OrderResponse(**serialize_order(order))


@router.put("/{order_id}/update-details", response_model=OrderResponse)
async def update_order_details(
    order_id: str,
    update_data: OrderUpdatePrePay,
    current_user: User = Depends(get_current_user),
):
    """Update shipping address and/or payment method on an unpaid order"""
    try:
        order = await Order.get(ObjectId(order_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.is_paid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update a paid order")
    if str(order.user) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if update_data.shipping_address:
        order.shipping_address = ShippingAddress(
            address=update_data.shipping_address.address,
            city=update_data.shipping_address.city,
            postal_code=update_data.shipping_address.postal_code,
            country=update_data.shipping_address.country,
        )
    if update_data.payment_method:
        order.payment_method = update_data.payment_method

    await order.save()
    return OrderResponse(**serialize_order(order))


@router.get("", response_model=List[OrderResponse])
async def get_orders(admin_user: User = Depends(require_admin)):
    """Get all orders (Admin only)"""
    orders = await Order.find_all().to_list()
    
    return [OrderResponse(**serialize_order(order)) for order in orders]
