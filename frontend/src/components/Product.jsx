import { Card, Button, ButtonGroup } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { addToCart, removeFromCart } from '../slices/cartSlice';
import { toast } from 'react-toastify';
import Rating from './Rating';

const Product = ({ product }) => {
  const dispatch = useDispatch();
  const cart = useSelector((state) => state.cart);
  const cartItem = cart.cartItems.find((x) => x._id === product._id);
  const currentQty = cartItem ? cartItem.qty : 0;

  const addToCartHandler = () => {
    if (currentQty < product.countInStock) {
      dispatch(addToCart({ ...product, qty: 1 }));
      toast.success(`${product.name} added!`, {
        autoClose: 500,
      });
    }
  };

  const decreaseQtyHandler = () => {
    if (currentQty > 1) {
      dispatch(addToCart({ ...product, qty: -1 }));
    } else if (currentQty === 1) {
      dispatch(removeFromCart(product._id));
      toast.info(`${product.name} removed from cart`, {
        autoClose: 500,
      });
    }
  };

  return (
    <Card className='my-3 p-3 rounded h-100 product-card'>
      <Link to={`/product/${product._id}`} className='product-card__link'>
        <Card.Img
          src={product.image}
          variant='top'
          className='product-card__image'
        />
      </Link>

      <Card.Body className='d-flex flex-column px-2 pt-3 pb-2'>
        <Link
          to={`/product/${product._id}`}
          className='product-card__link text-reset'
        >
          <Card.Title as='div' className='product-title mb-3'>
            <strong>{product.name}</strong>
          </Card.Title>
        </Link>

        {product.category && (
          <span className='category-pill mb-3'>{product.category}</span>
        )}

        <Card.Text as='div' className='mb-4'>
          <Rating
            value={product.rating}
            text={`${product.numReviews} reviews`}
          />
        </Card.Text>

        <div className='d-flex flex-column gap-3 mt-auto'>
          <p className='price-tag mb-0'>
            <span>${product.price}</span>
            <small>USD</small>
          </p>
          {currentQty === 0 ? (
            <Button
              onClick={addToCartHandler}
              variant='primary'
              className='w-100'
              disabled={product.countInStock === 0}
            >
              {product.countInStock === 0 ? 'Out of Stock' : 'Add to Cart'}
            </Button>
          ) : (
            <ButtonGroup className='w-100'>
              <Button
                variant='outline-secondary'
                onClick={decreaseQtyHandler}
                style={{ width: '35%' }}
              >
                -
              </Button>
              <Button
                variant='light'
                disabled
                style={{ width: '30%', color: '#000', fontWeight: 'bold' }}
              >
                {currentQty}
              </Button>
              <Button
                variant='outline-secondary'
                onClick={addToCartHandler}
                disabled={currentQty >= product.countInStock}
                style={{ width: '35%' }}
              >
                +
              </Button>
            </ButtonGroup>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default Product;
