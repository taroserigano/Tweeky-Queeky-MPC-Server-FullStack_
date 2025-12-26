/**
 * Header Component
 * 
 * Main navigation bar with responsive design and user authentication state.
 * Demonstrates best practices for:
 * - Redux state management (cart, auth)
 * - React Query mutations (logout)
 * - Theme switching functionality
 * - Conditional rendering based on user role
 * 
 * Features:
 * - Cart badge with item count
 * - User dropdown with profile/orders links
 * - Admin dropdown (conditional)
 * - Dark/Light theme toggle
 * - Secure logout with cache cleanup
 * 
 * @component
 * @param {Object} props
 * @param {string} props.theme - Current theme ('light' or 'dark')
 * @param {Function} props.onToggleTheme - Theme toggle handler
 */

import {
  Navbar,
  Nav,
  Container,
  NavDropdown,
  Badge,
  Button,
} from 'react-bootstrap';
import { FaShoppingCart, FaUser, FaMoon, FaSun } from 'react-icons/fa';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { useLogout } from '../hooks';
import { logout } from '../slices/authSlice';
import logo from '../assets/logo.svg';
import { resetCart } from '../slices/cartSlice';

const Header = ({ theme = 'light', onToggleTheme }) => {
  const { cartItems } = useSelector((state) => state.cart);
  const { userInfo } = useSelector((state) => state.auth);

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
          navigate('/login');
        },
        onError: (err) => {
          console.error('Logout failed:', err);
        },
      }
    );
  };

  return (
    <header>
      <Navbar
        variant='dark'
        expand='lg'
        collapseOnSelect
        className='navbar-modern'
      >
        <Container>
          <Navbar.Brand
            as={Link}
            to='/'
            className='brand-mark'
            style={{ gap: '24px' }}
          >
            <img src={logo} alt='Tweeky Queeky' className='brand-mark__logo' />
            Tweeky Queeky
          </Navbar.Brand>
          <Navbar.Toggle aria-controls='basic-navbar-nav' />
          <Navbar.Collapse
            id='basic-navbar-nav'
            className='justify-content-lg-end'
          >
            <Nav className='align-items-lg-center gap-2'>
              <Button
                variant='outline-light'
                size='sm'
                className='nav-pill theme-toggle-btn'
                onClick={onToggleTheme}
              >
                {theme === 'dark' ? <FaSun /> : <FaMoon />}{' '}
                {theme === 'dark' ? 'Light' : 'Dark'}
              </Button>
              <Nav.Link as={Link} to='/cart' className='nav-pill'>
                <FaShoppingCart /> Cart
                {cartItems.length > 0 && (
                  <Badge pill bg='success' style={{ marginLeft: '5px' }}>
                    {cartItems.reduce((a, c) => a + c.qty, 0)}
                  </Badge>
                )}
              </Nav.Link>
              {userInfo ? (
                <>
                  <NavDropdown
                    title={userInfo.name}
                    id='username'
                    className='nav-pill'
                    menuVariant='dark'
                  >
                    <NavDropdown.Item as={Link} to='/profile'>
                      Profile
                    </NavDropdown.Item>
                    <NavDropdown.Item onClick={logoutHandler}>
                      Logout
                    </NavDropdown.Item>
                  </NavDropdown>
                </>
              ) : (
                <Nav.Link as={Link} to='/login' className='nav-pill'>
                  <FaUser /> Sign In
                </Nav.Link>
              )}

              {/* Admin Links */}
              {userInfo && userInfo.isAdmin && (
                <NavDropdown
                  title='Admin'
                  id='adminmenu'
                  className='nav-pill'
                  menuVariant='dark'
                >
                  <NavDropdown.Item as={Link} to='/admin/productlist'>
                    Products
                  </NavDropdown.Item>
                  <NavDropdown.Item as={Link} to='/admin/orderlist'>
                    Orders
                  </NavDropdown.Item>
                  <NavDropdown.Item as={Link} to='/admin/userlist'>
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
