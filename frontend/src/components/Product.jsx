import { Card, Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { addToCart, removeFromCart } from "../slices/cartSlice";
import { FiMinus, FiPlus, FiShoppingBag, FiEye } from "react-icons/fi";
import Rating from "./Rating";

const Product = ({ product }) => {
  const dispatch = useDispatch();
  const cart = useSelector((state) => state.cart);
  const cartItem = cart.cartItems.find((x) => x._id === product._id);
  const currentQty = cartItem ? cartItem.qty : 0;

  const addToCartHandler = () => {
    if (currentQty < product.countInStock) {
      dispatch(addToCart({ ...product, qty: 1 }));
    }
  };

  const decreaseQtyHandler = () => {
    if (currentQty > 1) {
      dispatch(addToCart({ ...product, qty: -1 }));
    } else if (currentQty === 1) {
      dispatch(removeFromCart(product._id));
    }
  };

  return (
    <Card className="product-card h-100">
      <Link to={`/product/${product._id}`} className="product-card__link">
        <div className="product-card__image-wrapper">
          <Card.Img
            src={product.image}
            variant="top"
            className="product-card__image"
          />
          {product.countInStock === 0 && (
            <span className="stock-badge stock-badge--out">Out of Stock</span>
          )}
          <div className="product-card__overlay">
            <span className="product-card__quick-view">
              <FiEye /> Quick View
            </span>
          </div>
        </div>
      </Link>

      <Card.Body className="d-flex flex-column p-3">
        <div className="d-flex align-items-center gap-2 mb-2">
          {product.category && (
            <span className="category-pill">{product.category}</span>
          )}
          {product.countInStock > 0 && product.countInStock <= 5 && (
            <span className="stock-badge stock-badge--low">
              Only {product.countInStock} left
            </span>
          )}
        </div>

        <Link
          to={`/product/${product._id}`}
          className="product-card__link text-reset"
        >
          <Card.Title as="h3" className="product-title">
            {product.name}
          </Card.Title>
        </Link>

        <div className="mb-2 d-flex align-items-center gap-2">
          <Rating value={product.rating} />
          <span className="rating-score">
            {product.rating ? product.rating.toFixed(1) : "0.0"}
          </span>
          <span className="text-muted small">({product.numReviews})</span>
        </div>

        <div className="mt-auto">
          <div className="price-row mb-3">
            <p className="price-tag mb-0">${product.price}</p>
            {product.countInStock > 0 && (
              <span className="stock-indicator stock-indicator--in">
                In Stock
              </span>
            )}
          </div>

          {currentQty === 0 ? (
            <Button
              onClick={addToCartHandler}
              variant="primary"
              className="w-100 btn-cart"
              disabled={product.countInStock === 0}
            >
              <FiShoppingBag />
              {product.countInStock === 0 ? "Sold Out" : "Add to Cart"}
            </Button>
          ) : (
            <div className="qty-controls w-100">
              <button className="qty-btn" onClick={decreaseQtyHandler}>
                <FiMinus />
              </button>
              <span className="qty-display">{currentQty}</span>
              <button
                className="qty-btn"
                onClick={addToCartHandler}
                disabled={currentQty >= product.countInStock}
              >
                <FiPlus />
              </button>
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default Product;
