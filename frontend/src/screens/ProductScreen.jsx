import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { Row, Col, Image, Button, Form } from "react-bootstrap";
import { useProductDetails, useCreateReview } from "../hooks/useProductQueries";
import Rating from "../components/Rating";
import Loader, { PageLoader } from "../components/Loader";
import Message from "../components/Message";
import Meta from "../components/Meta";
import Breadcrumbs from "../components/Breadcrumbs";
import { addToCart, removeFromCart } from "../slices/cartSlice";
import {
  FiArrowLeft,
  FiShoppingBag,
  FiMinus,
  FiPlus,
  FiShoppingCart,
  FiPackage,
  FiTruck,
  FiShield,
  FiStar,
  FiUser,
  FiCheck,
  FiInfo,
} from "react-icons/fi";

const ProductScreen = () => {
  const { id: productId } = useParams();

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [activeTab, setActiveTab] = useState("reviews");

  const cart = useSelector((state) => state.cart);
  const cartItem = cart.cartItems.find((x) => x._id === productId);
  const currentQtyInCart = cartItem ? cartItem.qty : 0;

  const addToCartHandler = () => {
    dispatch(addToCart({ ...product, qty: 1 }));
  };

  const decreaseQtyHandler = () => {
    if (currentQtyInCart > 1) {
      dispatch(addToCart({ ...product, qty: -1 }));
    } else if (currentQtyInCart === 1) {
      dispatch(removeFromCart(product._id));
    }
  };

  const goToCartHandler = () => {
    navigate("/cart");
  };

  const {
    data: product,
    isLoading,
    refetch,
    error,
  } = useProductDetails(productId);

  const detailedDescription =
    product?.detailedDescription ||
    product?.detailed_description ||
    (product
      ? `${product.name}${product.brand ? ` by ${product.brand}` : ""} is designed for everyday use. ${product.description || ""}`
      : "");

  const { userInfo } = useSelector((state) => state.auth);

  const { mutate: createReview, isLoading: loadingProductReview } =
    useCreateReview();

  const hasSpecs =
    product?.specifications && Object.keys(product.specifications).length > 0;

  const submitHandler = async (e) => {
    e.preventDefault();

    createReview(
      { productId, rating: Number(rating), comment },
      {
        onSuccess: () => {
          refetch();
          setRating(0);
          setComment("");
        },
        onError: () => {},
      },
    );
  };

  return (
    <div className="product-page">
      {product && (
        <Breadcrumbs
          items={[
            { name: "Home", path: "/" },
            { name: product.category || "Products", path: "/" },
            { name: product.name, path: `/product/${productId}` },
          ]}
        />
      )}

      <Link className="back-link" to="/">
        <FiArrowLeft /> Back to Products
      </Link>

      {isLoading ? (
        <PageLoader text="Loading product details..." />
      ) : error ? (
        <Message variant="danger">
          {error?.response?.data?.detail ||
            error?.message ||
            "Failed to load product"}
        </Message>
      ) : (
        <>
          <Meta title={product.name} description={product.description} />

          {/* Main Product Section */}
          <div className="product-detail fade-in">
            <Row className="g-4 g-lg-5">
              {/* Product Image */}
              <Col lg={6}>
                <div className="product-detail__image-container">
                  <div className="product-detail__image-inner">
                    <Image
                      src={product.image}
                      alt={product.name}
                      fluid
                      className="product-detail__image"
                    />
                  </div>
                  {product.countInStock === 0 && (
                    <div className="product-detail__sold-out">Sold Out</div>
                  )}
                  {product.brand && (
                    <div className="product-detail__brand-tag">
                      {product.brand}
                    </div>
                  )}
                </div>
              </Col>

              {/* Product Info */}
              <Col lg={6}>
                <div className="product-detail__info">
                  {product.category && (
                    <span className="category-pill mb-3">
                      {product.category}
                    </span>
                  )}

                  <h1 className="product-detail__title">{product.name}</h1>

                  {product.sku && (
                    <div className="product-detail__sku">
                      SKU: {product.sku}
                    </div>
                  )}

                  <div className="product-detail__rating">
                    <Rating value={product.rating} />
                    <span className="product-detail__rating-score">
                      {product.rating ? product.rating.toFixed(1) : "0.0"}
                    </span>
                    <span className="product-detail__reviews-count">
                      ({product.numReviews}{" "}
                      {product.numReviews === 1 ? "review" : "reviews"})
                    </span>
                  </div>

                  <div className="product-detail__price">
                    <span className="product-detail__price-value">
                      ${product.price}
                    </span>
                    {product.countInStock > 0 ? (
                      <span className="product-detail__stock-pill product-detail__stock-pill--in">
                        <FiCheck /> In Stock ({product.countInStock})
                      </span>
                    ) : (
                      <span className="product-detail__stock-pill product-detail__stock-pill--out">
                        Out of Stock
                      </span>
                    )}
                  </div>

                  <p className="product-detail__description">
                    {product.description}
                  </p>

                  {/* Detailed Description - if available */}
                  {detailedDescription && (
                    <div className="product-detail__detailed-desc">
                      <h4>
                        <FiInfo /> About this item
                      </h4>
                      <p>{detailedDescription}</p>
                    </div>
                  )}

                  {/* Features */}
                  <div className="product-detail__features">
                    <div className="product-detail__feature">
                      <div className="product-detail__feature-icon">
                        <FiTruck />
                      </div>
                      <div>
                        <span className="product-detail__feature-title">
                          Free Shipping
                        </span>
                        <span className="product-detail__feature-desc">
                          Orders over $50
                        </span>
                      </div>
                    </div>
                    <div className="product-detail__feature">
                      <div className="product-detail__feature-icon">
                        <FiShield />
                      </div>
                      <div>
                        <span className="product-detail__feature-title">
                          Secure Checkout
                        </span>
                        <span className="product-detail__feature-desc">
                          SSL encrypted
                        </span>
                      </div>
                    </div>
                    <div className="product-detail__feature">
                      <div className="product-detail__feature-icon">
                        <FiPackage />
                      </div>
                      <div>
                        <span className="product-detail__feature-title">
                          Easy Returns
                        </span>
                        <span className="product-detail__feature-desc">
                          30-day policy
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Add to Cart Section */}
                  <div className="product-detail__actions">
                    {currentQtyInCart === 0 ? (
                      <Button
                        className="btn-cart btn-cart--large"
                        disabled={product.countInStock === 0}
                        onClick={addToCartHandler}
                      >
                        <FiShoppingBag />
                        {product.countInStock === 0
                          ? "Sold Out"
                          : "Add to Cart"}
                      </Button>
                    ) : (
                      <div className="product-detail__cart-controls">
                        <div className="qty-controls qty-controls--large">
                          <button
                            className="qty-btn"
                            onClick={decreaseQtyHandler}
                          >
                            <FiMinus />
                          </button>
                          <span className="qty-display">
                            {currentQtyInCart}
                          </span>
                          <button
                            className="qty-btn"
                            onClick={addToCartHandler}
                            disabled={currentQtyInCart >= product.countInStock}
                          >
                            <FiPlus />
                          </button>
                        </div>
                        <Button
                          variant="outline-primary"
                          className="btn-go-cart"
                          onClick={goToCartHandler}
                        >
                          <FiShoppingCart />
                          View Cart
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </Col>
            </Row>
          </div>

          {/* Tab Navigation for Specs & Reviews */}
          <div className="pdp-tabs fade-in">
            <div className="pdp-tabs__nav">
              {hasSpecs && (
                <button
                  className={`pdp-tabs__btn ${activeTab === "specs" ? "pdp-tabs__btn--active" : ""}`}
                  onClick={() => setActiveTab("specs")}
                >
                  <FiInfo /> Specifications
                </button>
              )}
              <button
                className={`pdp-tabs__btn ${activeTab === "reviews" ? "pdp-tabs__btn--active" : ""}`}
                onClick={() => setActiveTab("reviews")}
              >
                <FiStar /> Reviews ({product.reviews.length})
              </button>
            </div>

            {/* Specifications Tab */}
            {activeTab === "specs" && hasSpecs && (
              <div className="pdp-tabs__panel fade-in">
                <div className="specifications-grid">
                  {Object.entries(product.specifications).map(
                    ([key, value]) => (
                      <div key={key} className="specification-item">
                        <span className="specification-item__label">{key}</span>
                        <span className="specification-item__value">
                          {value}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>
            )}

            {/* Reviews Tab */}
            {activeTab === "reviews" && (
              <div className="pdp-tabs__panel fade-in">
                <Row className="g-4">
                  <Col lg={7}>
                    {product.reviews.length === 0 ? (
                      <div className="reviews-empty">
                        <FiStar className="reviews-empty__icon" />
                        <p>
                          No reviews yet. Be the first to review this product!
                        </p>
                      </div>
                    ) : (
                      <div className="reviews-list">
                        {product.reviews.map((review, idx) => (
                          <div
                            key={review._id}
                            className="review-card"
                            style={{ animationDelay: `${idx * 0.05}s` }}
                          >
                            <div className="review-card__header">
                              <div className="review-card__avatar">
                                <FiUser />
                              </div>
                              <div className="review-card__meta">
                                <strong className="review-card__name">
                                  {review.name}
                                </strong>
                                <span className="review-card__date">
                                  {new Date(
                                    review.createdAt,
                                  ).toLocaleDateString("en-US", {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                  })}
                                </span>
                              </div>
                              <div className="review-card__rating">
                                <Rating value={review.rating} />
                              </div>
                            </div>
                            <p className="review-card__comment">
                              {review.comment}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </Col>

                  <Col lg={5}>
                    <div className="review-form-card">
                      <h3 className="review-form-card__title">
                        Write a Review
                      </h3>

                      {loadingProductReview && <Loader />}

                      {userInfo ? (
                        <Form onSubmit={submitHandler}>
                          <Form.Group className="mb-3" controlId="rating">
                            <Form.Label>Your Rating</Form.Label>
                            <div className="rating-select">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                  key={star}
                                  type="button"
                                  className={`rating-select__star ${rating >= star ? "active" : ""}`}
                                  onClick={() => setRating(star)}
                                >
                                  <FiStar />
                                </button>
                              ))}
                            </div>
                          </Form.Group>

                          <Form.Group className="mb-3" controlId="comment">
                            <Form.Label>Your Review</Form.Label>
                            <Form.Control
                              as="textarea"
                              rows={4}
                              placeholder="Share your experience with this product..."
                              required
                              value={comment}
                              onChange={(e) => setComment(e.target.value)}
                              className="review-form-card__textarea"
                            />
                          </Form.Group>

                          <Button
                            disabled={loadingProductReview || !rating}
                            type="submit"
                            className="btn-cart w-100"
                          >
                            Submit Review
                          </Button>
                        </Form>
                      ) : (
                        <div className="review-form-card__signin">
                          <FiUser className="review-form-card__signin-icon" />
                          <p>Please sign in to write a review</p>
                          <Link to="/login" className="btn btn-primary">
                            Sign In
                          </Link>
                        </div>
                      )}
                    </div>
                  </Col>
                </Row>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ProductScreen;
