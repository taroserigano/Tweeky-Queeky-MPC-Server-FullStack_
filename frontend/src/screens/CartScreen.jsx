import { Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { Row, Col, Image } from "react-bootstrap";
import { addToCart, removeFromCart, clearCartItems } from "../slices/cartSlice";
import { useCreateOrder } from "../hooks/useOrderQueries";
import {
  FiShoppingCart,
  FiMinus,
  FiPlus,
  FiTrash2,
  FiArrowLeft,
  FiArrowRight,
  FiShield,
  FiTruck,
  FiTag,
} from "react-icons/fi";

const CartScreen = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const cart = useSelector((state) => state.cart);
  const { cartItems } = cart;
  const { userInfo } = useSelector((state) => state.auth);

  const { mutate: createOrder, isLoading: creatingOrder } = useCreateOrder();

  const increaseQty = (item) => {
    if (item.qty < item.countInStock) {
      dispatch(addToCart({ ...item, qty: 1 }));
    }
  };

  const decreaseQty = (item) => {
    if (item.qty > 1) {
      dispatch(addToCart({ ...item, qty: -1 }));
    } else {
      dispatch(removeFromCart(item._id));
    }
  };

  const removeFromCartHandler = (id) => {
    dispatch(removeFromCart(id));
  };

  const subtotal = cartItems.reduce(
    (acc, item) => acc + item.qty * item.price,
    0,
  );
  const itemCount = cartItems.reduce((acc, item) => acc + item.qty, 0);
  const shipping = subtotal > 50 ? 0 : 9.99;
  const total = subtotal + shipping;

  const checkoutHandler = () => {
    if (!userInfo) {
      navigate("/login?redirect=/checkout");
    } else {
      navigate("/checkout");
    }
  };

  return (
    <div className="cart-page fade-in">
      <div className="cart-page__header">
        <div>
          <h1 className="cart-page__title">
            <FiShoppingCart /> Shopping Cart
          </h1>
          <p className="cart-page__subtitle">
            {itemCount > 0
              ? `${itemCount} item${itemCount !== 1 ? "s" : ""} in your cart`
              : "Your cart is empty"}
          </p>
        </div>
        <Link to="/" className="back-link">
          <FiArrowLeft /> Continue Shopping
        </Link>
      </div>

      {cartItems.length === 0 ? (
        <div className="cart-empty">
          <div className="cart-empty__icon">
            <FiShoppingCart />
          </div>
          <h2 className="cart-empty__title">Your cart is empty</h2>
          <p className="cart-empty__text">
            Looks like you haven't added anything to your cart yet.
          </p>
          <Link to="/" className="btn-cart">
            <FiArrowLeft /> Start Shopping
          </Link>
        </div>
      ) : (
        <Row className="g-4">
          <Col lg={8}>
            <div className="cart-items">
              {cartItems.map((item, idx) => (
                <div
                  className="cart-item"
                  key={item._id}
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  <Link
                    to={`/product/${item._id}`}
                    className="cart-item__image-link"
                  >
                    <Image
                      src={item.image}
                      alt={item.name}
                      className="cart-item__image"
                    />
                  </Link>

                  <div className="cart-item__details">
                    <Link
                      to={`/product/${item._id}`}
                      className="cart-item__name"
                    >
                      {item.name}
                    </Link>
                    {item.category && (
                      <span className="cart-item__category">
                        {item.category}
                      </span>
                    )}
                    <span className="cart-item__price-mobile">
                      ${(item.price * item.qty).toFixed(2)}
                    </span>
                  </div>

                  <div className="cart-item__qty">
                    <div className="qty-controls">
                      <button
                        className="qty-btn"
                        onClick={() => decreaseQty(item)}
                      >
                        <FiMinus />
                      </button>
                      <span className="qty-display">{item.qty}</span>
                      <button
                        className="qty-btn"
                        onClick={() => increaseQty(item)}
                        disabled={item.qty >= item.countInStock}
                      >
                        <FiPlus />
                      </button>
                    </div>
                  </div>

                  <div className="cart-item__price">
                    ${(item.price * item.qty).toFixed(2)}
                    {item.qty > 1 && (
                      <span className="cart-item__unit-price">
                        ${item.price.toFixed(2)} each
                      </span>
                    )}
                  </div>

                  <button
                    className="cart-item__remove"
                    onClick={() => removeFromCartHandler(item._id)}
                    title="Remove item"
                  >
                    <FiTrash2 />
                  </button>
                </div>
              ))}
            </div>
          </Col>

          <Col lg={4}>
            <div className="cart-summary">
              <h3 className="cart-summary__title">Order Summary</h3>

              <div className="cart-summary__rows">
                <div className="cart-summary__row">
                  <span>Subtotal ({itemCount} items)</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="cart-summary__row">
                  <span>Shipping</span>
                  <span className={shipping === 0 ? "cart-summary__free" : ""}>
                    {shipping === 0 ? "FREE" : `$${shipping.toFixed(2)}`}
                  </span>
                </div>
                {shipping > 0 && (
                  <div className="cart-summary__shipping-note">
                    <FiTruck /> Add ${(50 - subtotal).toFixed(2)} more for free
                    shipping
                  </div>
                )}
                <div className="cart-summary__divider" />
                <div className="cart-summary__row cart-summary__row--total">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>

              <button
                className="cart-summary__checkout"
                disabled={cartItems.length === 0 || creatingOrder}
                onClick={checkoutHandler}
              >
                {creatingOrder ? (
                  "Creating Order..."
                ) : (
                  <>
                    Proceed to Checkout <FiArrowRight />
                  </>
                )}
              </button>

              <div className="cart-summary__badges">
                <div className="cart-summary__badge">
                  <FiShield /> Secure Checkout
                </div>
                <div className="cart-summary__badge">
                  <FiTag /> Best Price Guarantee
                </div>
              </div>
            </div>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default CartScreen;
