import {
  Navbar,
  Nav,
  Container,
  NavDropdown,
  Badge,
  Button,
} from "react-bootstrap";
import { FaShoppingCart, FaUser, FaMoon, FaSun, FaRobot } from "react-icons/fa";
import { HiCube } from "react-icons/hi";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import { useLogout } from "../hooks";
import { logout } from "../slices/authSlice";
import { resetCart } from "../slices/cartSlice";
import { useTheme } from "../contexts/ThemeContext";

const Header = () => {
  const { cartItems } = useSelector((state) => state.cart);
  const { userInfo } = useSelector((state) => state.auth);
  const { theme, toggleTheme } = useTheme();

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { mutate: logoutApiCall } = useLogout();

  const logoutHandler = async () => {
    logoutApiCall(
      {},
      {
        onSuccess: () => {
          dispatch(logout());
          dispatch(resetCart());
          navigate("/login");
        },
        onError: (err) => {
          console.error("Logout failed:", err);
        },
      },
    );
  };

  const totalItems = cartItems.reduce((a, c) => a + c.qty, 0);

  return (
    <header>
      <Navbar
        variant={theme === "dark" ? "dark" : "light"}
        expand="lg"
        collapseOnSelect
        className="navbar-modern"
      >
        <Container>
          <Navbar.Brand as={Link} to="/" className="brand-mark">
            <div className="brand-logo__icon">
              <HiCube />
            </div>
            <span className="brand-mark__text">
              Tweeky <span className="brand-mark__accent">Queeky</span>
            </span>
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="basic-navbar-nav" />

          <Navbar.Collapse
            id="basic-navbar-nav"
            className="justify-content-lg-end"
          >
            <Nav className="align-items-lg-center gap-1">
              {/* Theme Toggle */}
              <Button
                variant="link"
                className="theme-toggle-btn"
                onClick={toggleTheme}
                aria-label="Toggle theme"
              >
                {theme === "dark" ? <FaSun /> : <FaMoon />}
              </Button>

              {/* AI Assistant */}
              <Nav.Link as={Link} to="/ai" className="nav-pill nav-pill--ai">
                <FaRobot />
                <span className="d-none d-md-inline ms-2">AI Hub</span>
              </Nav.Link>

              {/* Cart */}
              <Nav.Link
                as={Link}
                to="/cart"
                className="nav-pill nav-pill--cart"
              >
                <FaShoppingCart />
                <span className="d-none d-md-inline ms-2">Cart</span>
                {totalItems > 0 && (
                  <Badge pill className="cart-badge">
                    {totalItems}
                  </Badge>
                )}
              </Nav.Link>

              {/* User Menu */}
              {userInfo ? (
                <NavDropdown
                  title={
                    <span className="d-inline-flex align-items-center gap-2">
                      <span className="user-avatar">
                        {userInfo.name.charAt(0).toUpperCase()}
                      </span>
                      <span className="d-none d-md-inline">
                        {userInfo.name}
                      </span>
                    </span>
                  }
                  id="username"
                  className="nav-pill"
                  align="end"
                >
                  <NavDropdown.Item as={Link} to="/profile">
                    Profile
                  </NavDropdown.Item>
                  <NavDropdown.Divider />
                  <NavDropdown.Item onClick={logoutHandler}>
                    Logout
                  </NavDropdown.Item>
                </NavDropdown>
              ) : (
                <Nav.Link as={Link} to="/login" className="nav-pill">
                  <FaUser />
                  <span className="ms-2">Sign In</span>
                </Nav.Link>
              )}

              {/* Admin Menu */}
              {userInfo && userInfo.isAdmin && (
                <NavDropdown
                  title={
                    <span className="d-inline-flex align-items-center gap-1">
                      <span className="admin-badge">ADMIN</span>
                    </span>
                  }
                  id="adminmenu"
                  className="nav-pill"
                  align="end"
                >
                  <NavDropdown.Item as={Link} to="/admin/productlist">
                    Products
                  </NavDropdown.Item>
                  <NavDropdown.Item as={Link} to="/admin/orderlist">
                    Orders
                  </NavDropdown.Item>
                  <NavDropdown.Item as={Link} to="/admin/userlist">
                    Users
                  </NavDropdown.Item>
                </NavDropdown>
              )}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
    </header>
  );
};

export default Header;
