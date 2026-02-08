import { Link } from "react-router-dom";
import { Image } from "react-bootstrap";
import {
  FiChevronLeft,
  FiChevronRight,
  FiStar,
  FiArrowRight,
} from "react-icons/fi";
import { useState, useEffect, useCallback, useRef } from "react";
import Message from "./Message";
import { useTopProducts } from "../hooks/useProductQueries";

const CarouselSkeleton = () => (
  <div className="hero-carousel hero-carousel--skeleton">
    <div className="hero-carousel__bg">
      <div className="hero-carousel__orb hero-carousel__orb--1"></div>
      <div className="hero-carousel__orb hero-carousel__orb--2"></div>
    </div>
    <div className="hero-carousel__skeleton-content">
      <div className="hero-carousel__skeleton-spinner"></div>
      <p className="hero-carousel__skeleton-text">
        Loading featured products...
      </p>
    </div>
  </div>
);

const ProductCarousel = () => {
  const { data: products, isLoading, error } = useTopProducts();
  const [activeIndex, setActiveIndex] = useState(0);
  const [prevIndex, setPrevIndex] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const imageCache = useRef(new Set());
  const [imagesPreloaded, setImagesPreloaded] = useState(false);
  const timerRef = useRef(null);

  const goToSlide = useCallback(
    (index) => {
      if (isAnimating || !products || index === activeIndex) return;
      setIsAnimating(true);
      setPrevIndex(activeIndex);
      setActiveIndex(index);
      setTimeout(() => {
        setPrevIndex(null);
        setIsAnimating(false);
      }, 600);
    },
    [isAnimating, products, activeIndex],
  );

  const nextSlide = useCallback(() => {
    if (!products) return;
    goToSlide((activeIndex + 1) % products.length);
  }, [activeIndex, products, goToSlide]);

  const prevSlide = useCallback(() => {
    if (!products) return;
    goToSlide(activeIndex === 0 ? products.length - 1 : activeIndex - 1);
  }, [activeIndex, products, goToSlide]);

  // Preload all carousel images on mount
  useEffect(() => {
    if (!products || products.length === 0) return;

    const preloadImages = async () => {
      const promises = products.map(
        (p) =>
          new Promise((resolve) => {
            if (imageCache.current.has(p.image)) return resolve();
            const img = new window.Image();
            img.onload = () => {
              imageCache.current.add(p.image);
              resolve();
            };
            img.onerror = () => resolve();
            img.src = p.image;
          }),
      );
      await Promise.all(promises);
      setImagesPreloaded(true);
    };

    preloadImages();
  }, [products]);

  // Auto-advance
  useEffect(() => {
    if (!products || products.length === 0 || !imagesPreloaded) return;
    timerRef.current = setInterval(nextSlide, 6000);
    return () => clearInterval(timerRef.current);
  }, [products, nextSlide, imagesPreloaded]);

  if (isLoading) return <CarouselSkeleton />;
  if (error)
    return (
      <Message variant="danger">{error?.data?.message || error.error}</Message>
    );
  if (!products || products.length === 0) return null;

  const getSlideClass = (i) => {
    if (i === activeIndex) return "hero-slide hero-slide--active";
    if (i === prevIndex) return "hero-slide hero-slide--leaving";
    return "hero-slide";
  };

  return (
    <div className="hero-carousel">
      {/* Animated background */}
      <div className="hero-carousel__bg">
        <div className="hero-carousel__orb hero-carousel__orb--1"></div>
        <div className="hero-carousel__orb hero-carousel__orb--2"></div>
        <div className="hero-carousel__orb hero-carousel__orb--3"></div>
      </div>

      {/* All slides stacked */}
      <div className="hero-carousel__stage">
        {products.map((product, i) => (
          <div className={getSlideClass(i)} key={product._id}>
            {/* Left: info */}
            <div className="hero-slide__info">
              <span className="hero-carousel__badge">
                <FiStar /> Featured Product
              </span>
              <h2 className="hero-carousel__title">{product.name}</h2>
              <p className="hero-carousel__desc">
                {product.description?.length > 120
                  ? product.description.substring(0, 120) + "..."
                  : product.description}
              </p>
              <div className="hero-carousel__meta">
                <span className="hero-carousel__price">${product.price}</span>
                <span className="hero-carousel__rating">
                  <FiStar className="hero-carousel__star-icon" />
                  {product.rating?.toFixed(1)}
                  <span className="hero-carousel__reviews">
                    ({product.numReviews})
                  </span>
                </span>
              </div>
              <Link
                to={`/product/${product._id}`}
                className="hero-carousel__cta"
                tabIndex={i === activeIndex ? 0 : -1}
              >
                Shop Now <FiArrowRight />
              </Link>
            </div>

            {/* Right: image */}
            <div className="hero-slide__image-wrap">
              <div className="hero-carousel__image-glow"></div>
              <Image
                src={product.image}
                alt={product.name}
                className="hero-carousel__image"
                loading="eager"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Bottom controls */}
      <div className="hero-carousel__controls">
        <button
          className="hero-carousel__arrow"
          onClick={prevSlide}
          aria-label="Previous"
        >
          <FiChevronLeft />
        </button>
        <div className="hero-carousel__dots">
          {products.map((_, i) => (
            <button
              key={i}
              className={`hero-carousel__dot ${i === activeIndex ? "hero-carousel__dot--active" : ""}`}
              onClick={() => goToSlide(i)}
              aria-label={`Go to slide ${i + 1}`}
            />
          ))}
        </div>
        <button
          className="hero-carousel__arrow"
          onClick={nextSlide}
          aria-label="Next"
        >
          <FiChevronRight />
        </button>
      </div>

      {/* Slide counter */}
      <div className="hero-carousel__counter">
        <span className="hero-carousel__counter-current">
          {String(activeIndex + 1).padStart(2, "0")}
        </span>
        <span className="hero-carousel__counter-sep">/</span>
        <span className="hero-carousel__counter-total">
          {String(products.length).padStart(2, "0")}
        </span>
      </div>
    </div>
  );
};

export default ProductCarousel;
