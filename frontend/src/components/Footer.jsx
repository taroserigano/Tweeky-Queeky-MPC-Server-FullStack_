import { Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import { HiCube } from "react-icons/hi";
import { FiShoppingBag, FiCpu, FiShield, FiTruck } from "react-icons/fi";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer>
      {/* Trust badges strip */}
      <div className="footer-trust">
        <Container>
          <div className="footer-trust__grid">
            <div className="footer-trust__item">
              <FiTruck />
              <span>Free Shipping</span>
            </div>
            <div className="footer-trust__item">
              <FiShield />
              <span>Secure Payment</span>
            </div>
            <div className="footer-trust__item">
              <FiCpu />
              <span>AI-Powered Search</span>
            </div>
            <div className="footer-trust__item">
              <FiShoppingBag />
              <span>Premium Products</span>
            </div>
          </div>
        </Container>
      </div>

      {/* Main footer */}
      <div className="footer-main">
        <Container>
          <div className="footer-content">
            <div className="footer-brand">
              <div className="footer-brand__icon">
                <HiCube />
              </div>
              <div>
                <span className="footer-brand__text">Tweeky Queeky</span>
                <p className="footer-brand__tagline">
                  Premium Audio & Tech Store
                </p>
              </div>
            </div>
            <div className="footer-links">
              <Link to="/" className="footer-link">
                Home
              </Link>
              <Link to="/ai" className="footer-link">
                AI Hub
              </Link>
              <Link to="/cart" className="footer-link">
                Cart
              </Link>
              <Link to="/login" className="footer-link">
                Account
              </Link>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; {currentYear} Tweeky Queeky. All Rights Reserved.</p>
          </div>
        </Container>
      </div>
    </footer>
  );
};

export default Footer;
