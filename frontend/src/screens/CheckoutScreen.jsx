import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Button,
  Row,
  Col,
  ListGroup,
  Image,
  Card,
  Form,
} from "react-bootstrap";
import { useDispatch, useSelector } from "react-redux";
import Message from "../components/Message";
import Loader from "../components/Loader";
import { getErrorMessage } from "../utils/errorUtils";
import { useCreateOrder } from "../hooks/useOrderQueries";
import {
  saveShippingAddress,
  savePaymentMethod,
  clearCartItems,
} from "../slices/cartSlice";

const CheckoutScreen = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const cart = useSelector((state) => state.cart);
  const shippingAddress = cart.shippingAddress || {};

  // Shipping address state
  const [address, setAddress] = useState(shippingAddress.address || "");
  const [city, setCity] = useState(shippingAddress.city || "");
  const [postalCode, setPostalCode] = useState(
    shippingAddress.postalCode || "",
  );
  const [country, setCountry] = useState(shippingAddress.country || "");

  // Payment method state
  const [paymentMethod, setPaymentMethod] = useState(
    cart.paymentMethod || "PayPal",
  );

  const { mutate: createOrder, isLoading, error } = useCreateOrder();

  const placeOrderHandler = () => {
    // Validate shipping
    if (!address || !city || !postalCode || !country) {
      return;
    }

    // Save shipping & payment to redux before placing order
    dispatch(saveShippingAddress({ address, city, postalCode, country }));
    dispatch(savePaymentMethod(paymentMethod));

    // Map cart items to order items format
    const orderItems = cart.cartItems.map((item) => ({
      name: item.name,
      qty: item.qty,
      image: item.image,
      price: item.price,
      product: item._id || item.product, // Use _id as product ID
    }));

    const orderPayload = {
      orderItems,
      shippingAddress: { address, city, postalCode, country },
      paymentMethod,
    };

    console.log(
      "Placing order with payload:",
      JSON.stringify(orderPayload, null, 2),
    );

    createOrder(orderPayload, {
      onSuccess: (res) => {
        dispatch(clearCartItems());
        navigate(`/order/${res._id}`);
      },
      onError: () => {},
    });
  };

  return (
    <Row>
      <Col md={8}>
        <ListGroup variant="flush">
          {/* ── Shipping Address ── */}
          <ListGroup.Item>
            <h2>Shipping Address</h2>
            <Row className="mb-2">
              <Col sm={12}>
                <Form.Group controlId="address" className="mb-2">
                  <Form.Label>Address</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row className="mb-2">
              <Col sm={6}>
                <Form.Group controlId="city" className="mb-2">
                  <Form.Label>City</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter city"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                  />
                </Form.Group>
              </Col>
              <Col sm={6}>
                <Form.Group controlId="postalCode" className="mb-2">
                  <Form.Label>Postal Code</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter postal code"
                    value={postalCode}
                    onChange={(e) => setPostalCode(e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col sm={6}>
                <Form.Group controlId="country" className="mb-2">
                  <Form.Label>Country</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter country"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>
          </ListGroup.Item>

          {/* ── Payment Method ── */}
          <ListGroup.Item>
            <h2>Payment Method</h2>
            <Form.Group>
              <Col>
                <Form.Check
                  className="my-2"
                  type="radio"
                  label="PayPal or Credit Card"
                  id="PayPal"
                  name="paymentMethod"
                  value="PayPal"
                  checked={paymentMethod === "PayPal"}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <Form.Check
                  className="my-2"
                  type="radio"
                  label="Stripe (Credit / Debit Card)"
                  id="Stripe"
                  name="paymentMethod"
                  value="Stripe"
                  checked={paymentMethod === "Stripe"}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
              </Col>
            </Form.Group>
          </ListGroup.Item>

          {/* ── Order Items ── */}
          <ListGroup.Item>
            <h2>Order Items</h2>
            {cart.cartItems.length === 0 ? (
              <Message>Your cart is empty</Message>
            ) : (
              <ListGroup variant="flush">
                {cart.cartItems.map((item, index) => (
                  <ListGroup.Item key={index}>
                    <Row className="align-items-center">
                      <Col md={1}>
                        <Image src={item.image} alt={item.name} fluid rounded />
                      </Col>
                      <Col>
                        <Link to={`/product/${item.product}`}>{item.name}</Link>
                      </Col>
                      <Col md={4}>
                        {item.qty} x ${item.price} = $
                        {(item.qty * (item.price * 100)) / 100}
                      </Col>
                    </Row>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            )}
          </ListGroup.Item>
        </ListGroup>
      </Col>

      {/* ── Order Summary ── */}
      <Col md={4}>
        <Card>
          <ListGroup variant="flush">
            <ListGroup.Item>
              <h2>Order Summary</h2>
            </ListGroup.Item>
            <ListGroup.Item>
              <Row>
                <Col>Items</Col>
                <Col>${cart.itemsPrice}</Col>
              </Row>
            </ListGroup.Item>
            <ListGroup.Item>
              <Row>
                <Col>Shipping</Col>
                <Col>${cart.shippingPrice}</Col>
              </Row>
            </ListGroup.Item>
            <ListGroup.Item>
              <Row>
                <Col>Tax</Col>
                <Col>${cart.taxPrice}</Col>
              </Row>
            </ListGroup.Item>
            <ListGroup.Item>
              <Row>
                <Col>Total</Col>
                <Col>${cart.totalPrice}</Col>
              </Row>
            </ListGroup.Item>
            <ListGroup.Item>
              {error && (
                <Message variant="danger">
                  {getErrorMessage(error, "An error occurred")}
                </Message>
              )}
            </ListGroup.Item>
            <ListGroup.Item>
              <Button
                type="button"
                className="btn-block w-100"
                disabled={cart.cartItems.length === 0}
                onClick={placeOrderHandler}
              >
                Place Order
              </Button>
              {isLoading && <Loader />}
            </ListGroup.Item>
          </ListGroup>
        </Card>
      </Col>
    </Row>
  );
};

export default CheckoutScreen;
