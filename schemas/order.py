from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Any
from datetime import datetime


# Embedded schemas
class ShippingAddressSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    address: str
    city: str
    postal_code: str = Field(alias="postalCode")
    country: str


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: str
    qty: int
    image: str
    price: float
    product: str

    @model_validator(mode='before')
    @classmethod
    def set_product_from_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If _id is provided but product is not, use _id as product
            if '_id' in data and 'product' not in data:
                data['product'] = str(data['_id'])
        return data


class PaymentResultSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = None
    status: Optional[str] = None
    update_time: Optional[str] = Field(None, alias="update_time")
    email_address: Optional[str] = Field(None, alias="email_address")


# Request schemas
class OrderCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    order_items: List[OrderItemSchema] = Field(alias="orderItems")
    shipping_address: ShippingAddressSchema = Field(alias="shippingAddress")
    payment_method: str = Field(alias="paymentMethod")


class OrderUpdatePrePay(BaseModel):
    """Update shipping address and/or payment method on an unpaid order."""
    model_config = ConfigDict(populate_by_name=True)

    shipping_address: Optional[ShippingAddressSchema] = Field(None, alias="shippingAddress")
    payment_method: Optional[str] = Field(None, alias="paymentMethod")


class OrderPaymentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow', arbitrary_types_allowed=True)
    
    # Make ALL fields optional with defaults to accept any PayPal response structure
    id: Optional[str] = None
    status: Optional[str] = None
    update_time: Optional[str] = None
    email_address: Optional[str] = None
    
    # PayPal payer object (optional)
    payer: Optional[dict] = None
    
    # Additional PayPal fields (all optional)
    create_time: Optional[str] = None
    purchase_units: Optional[List[dict]] = None
    links: Optional[List[dict]] = None
    intent: Optional[str] = None
    
    # Allow any other fields PayPal might send
    model_config = ConfigDict(extra='allow', populate_by_name=True)


# Response schemas
class OrderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str = Field(alias="_id")
    user: str
    order_items: List[dict] = Field(alias="orderItems")
    shipping_address: dict = Field(alias="shippingAddress")
    payment_method: str = Field(alias="paymentMethod")
    payment_result: Optional[dict] = Field(None, alias="paymentResult")
    items_price: float = Field(alias="itemsPrice")
    tax_price: float = Field(alias="taxPrice")
    shipping_price: float = Field(alias="shippingPrice")
    total_price: float = Field(alias="totalPrice")
    is_paid: bool = Field(alias="isPaid")
    paid_at: Optional[datetime] = Field(None, alias="paidAt")
    is_delivered: bool = Field(alias="isDelivered")
    delivered_at: Optional[datetime] = Field(None, alias="deliveredAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
