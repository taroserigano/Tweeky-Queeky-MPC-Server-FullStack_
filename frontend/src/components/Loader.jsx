import { Spinner } from "react-bootstrap";

const Loader = ({ size = "lg", text = "" }) => {
  const sizeMap = {
    sm: { width: "24px", height: "24px" },
    md: { width: "48px", height: "48px" },
    lg: { width: "80px", height: "80px" },
  };

  const dimensions = sizeMap[size] || sizeMap.lg;

  return (
    <div className="loader-container">
      <div className="loader-spinner">
        <Spinner
          animation="border"
          role="status"
          style={{
            width: dimensions.width,
            height: dimensions.height,
            color: "var(--primary-500)",
            borderWidth: size === "sm" ? "2px" : "3px",
          }}
        />
      </div>
      {text && <p className="loader-text">{text}</p>}
    </div>
  );
};

// Full page loader with overlay
export const PageLoader = ({ text = "Loading..." }) => {
  return (
    <div className="page-loader">
      <div className="page-loader__content">
        <div className="page-loader__spinner"></div>
        <p className="page-loader__text">{text}</p>
      </div>
    </div>
  );
};

// Skeleton loader for cards
export const SkeletonCard = () => {
  return (
    <div className="skeleton-card">
      <div className="skeleton-card__image skeleton-pulse"></div>
      <div className="skeleton-card__body">
        <div className="skeleton-card__badge skeleton-pulse"></div>
        <div className="skeleton-card__title skeleton-pulse"></div>
        <div className="skeleton-card__rating skeleton-pulse"></div>
        <div className="skeleton-card__price skeleton-pulse"></div>
        <div className="skeleton-card__button skeleton-pulse"></div>
      </div>
    </div>
  );
};

// Skeleton grid for product listing
export const SkeletonGrid = ({ count = 8 }) => {
  return (
    <div className="products-grid">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  );
};

// Inline loader for buttons
export const ButtonLoader = () => {
  return (
    <Spinner
      as="span"
      animation="border"
      size="sm"
      role="status"
      aria-hidden="true"
      style={{ marginRight: "0.5rem" }}
    />
  );
};

// Product detail skeleton
export const ProductDetailSkeleton = () => {
  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-md-6">
          <div style={{
            width: "100%",
            height: "500px",
            backgroundColor: "#e0e0e0",
            borderRadius: "12px",
            animation: "pulse 1.5s ease-in-out infinite"
          }} />
        </div>
        <div className="col-md-6">
          <div style={{ marginBottom: "16px", height: "40px", width: "60%", backgroundColor: "#e0e0e0", borderRadius: "8px", animation: "pulse 1.5s ease-in-out infinite" }} />
          <div style={{ marginBottom: "16px", height: "24px", width: "40%", backgroundColor: "#e0e0e0", borderRadius: "8px", animation: "pulse 1.5s ease-in-out infinite" }} />
          <div style={{ marginBottom: "16px", height: "32px", width: "30%", backgroundColor: "#e0e0e0", borderRadius: "8px", animation: "pulse 1.5s ease-in-out infinite" }} />
          <div style={{ marginBottom: "24px", height: "100px", width: "100%", backgroundColor: "#e0e0e0", borderRadius: "8px", animation: "pulse 1.5s ease-in-out infinite" }} />
          <div style={{ marginBottom: "16px", height: "48px", width: "150px", backgroundColor: "#e0e0e0", borderRadius: "8px", animation: "pulse 1.5s ease-in-out infinite" }} />
        </div>
      </div>
    </div>
  );
};

// Table skeleton for admin screens
export const TableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="table-responsive">
      <table className="table">
        <thead>
          <tr>
            {Array.from({ length: columns }).map((_, idx) => (
              <th key={idx}>
                <div style={{ height: "24px", width: "80%", backgroundColor: "#e0e0e0", borderRadius: "4px", animation: "pulse 1.5s ease-in-out infinite" }} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIdx) => (
            <tr key={rowIdx}>
              {Array.from({ length: columns }).map((_, colIdx) => (
                <td key={colIdx}>
                  <div style={{ height: "20px", width: "90%", backgroundColor: "#e0e0e0", borderRadius: "4px", animation: "pulse 1.5s ease-in-out infinite" }} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Loader;
