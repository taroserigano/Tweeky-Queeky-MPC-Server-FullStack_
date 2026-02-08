import React from "react";
import { Link } from "react-router-dom";
import { FiHome, FiChevronRight } from "react-icons/fi";
import { useLocation } from "react-router-dom";

const Breadcrumbs = ({ items }) => {
  const location = useLocation();

  const getBreadcrumbs = () => {
    if (items) return items;

    const pathSegments = location.pathname.split("/").filter((x) => x);
    const breadcrumbs = [{ name: "Home", path: "/" }];

    pathSegments.forEach((segment, index) => {
      const path = `/${pathSegments.slice(0, index + 1).join("/")}`;
      const name = segment
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");

      breadcrumbs.push({ name, path });
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumbs__list">
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;

          return (
            <li
              key={crumb.path}
              className={`breadcrumbs__item ${isLast ? "breadcrumbs__item--active" : ""}`}
            >
              {!isLast && index > 0 && (
                <FiChevronRight className="breadcrumbs__separator" />
              )}
              {isLast ? (
                <span className="breadcrumbs__current">{crumb.name}</span>
              ) : (
                <>
                  <Link to={crumb.path} className="breadcrumbs__link">
                    {index === 0 && (
                      <FiHome className="breadcrumbs__home-icon" />
                    )}
                    {crumb.name}
                  </Link>
                  {index === 0 && (
                    <FiChevronRight className="breadcrumbs__separator" />
                  )}
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumbs;
