import { Container, Form } from "react-bootstrap";
import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { useProducts } from "../hooks/useProductQueries";
import {
  FiArrowLeft,
  FiGrid,
  FiPackage,
  FiTrendingUp,
  FiFilter,
} from "react-icons/fi";
import Product from "../components/Product";
import { SkeletonGrid } from "../components/Loader";
import Message from "../components/Message";
import Paginate from "../components/Paginate";
import ProductCarousel from "../components/ProductCarousel";
import Meta from "../components/Meta";
import SearchBox from "../components/SearchBox";
import ChatbotWidget from "../components/ChatbotWidget";

const HomeScreen = () => {
  const { pageNumber, keyword } = useParams();
  const [sortBy, setSortBy] = useState("");

  const { data, isLoading, error } = useProducts(keyword, pageNumber, sortBy);

  return (
    <>
      {!keyword ? (
        <ProductCarousel />
      ) : (
        <Link to="/" className="back-link">
          <FiArrowLeft /> Back to Products
        </Link>
      )}

      {/* Search Section */}
      <div className="search-section">
        <Container style={{ maxWidth: "580px" }}>
          <SearchBox />
        </Container>
      </div>

      {isLoading ? (
        <>
          <div className="section-header mt-4">
            <div className="section-header__left">
              <div className="section-icon section-icon--pulse">
                <FiPackage />
              </div>
              <div>
                <h1 className="section-header__title">Loading Products...</h1>
                <p className="section-header__subtitle">Please wait</p>
              </div>
            </div>
          </div>
          <SkeletonGrid count={8} />
        </>
      ) : error ? (
        <Message variant="danger">
          {error?.response?.data?.detail ||
            error?.response?.data?.message ||
            error?.message ||
            "Failed to load products"}
        </Message>
      ) : (
        <>
          <Meta />

          {/* Section Header */}
          <div className="section-header mt-4">
            <div className="section-header__left">
              <div className="section-icon">
                {keyword ? <FiGrid /> : <FiTrendingUp />}
              </div>
              <div>
                <h1 className="section-header__title">
                  {keyword ? `Results for "${keyword}"` : "Latest Products"}
                </h1>
                <p className="section-header__subtitle">
                  {data.products.length}{" "}
                  {data.products.length === 1 ? "product" : "products"} found
                </p>
              </div>
            </div>
            {/* Sort Dropdown */}
            <div className="section-header__right">
              <div className="filter-group">
                <FiFilter className="filter-icon" />
                <Form.Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="sort-select"
                >
                  <option value="">Sort by: Default</option>
                  <option value="newest">Newest First</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="rating_desc">Highest Rated</option>
                </Form.Select>
              </div>
            </div>
          </div>

          {/* Products Grid */}
          <div className="products-grid fade-in">
            {data.products.map((product, index) => (
              <div
                key={product._id}
                className="products-grid__item"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <Product product={product} />
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="d-flex justify-content-center mt-5">
              <Paginate
                pages={data.pages}
                page={data.page}
                keyword={keyword ? keyword : ""}
              />
            </div>
          )}
        </>
      )}

      {/* Chatbot Widget - Fixed Lower Left */}
      <ChatbotWidget />
    </>
  );
};

export default HomeScreen;
