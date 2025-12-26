import React, { useState, useEffect } from 'react';
import { Form, Button } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

const SearchBox = () => {
  const navigate = useNavigate();
  const { keyword: urlKeyword } = useParams();

  // FIX: uncontrolled input - urlKeyword may be undefined
  const [keyword, setKeyword] = useState(urlKeyword || '');
  const [debouncedKeyword, setDebouncedKeyword] = useState(keyword);

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedKeyword(keyword);
    }, 400);

    return () => {
      clearTimeout(timer);
    };
  }, [keyword]);

  // Auto-search on debounced keyword change
  useEffect(() => {
    if (debouncedKeyword) {
      navigate(`/search/${debouncedKeyword.trim()}`);
    } else if (urlKeyword) {
      navigate('/');
    }
  }, [debouncedKeyword, navigate, urlKeyword]);

  const submitHandler = (e) => {
    e.preventDefault();
    if (keyword) {
      navigate(`/search/${keyword.trim()}`);
    } else {
      navigate('/');
    }
  };

  return (
    <Form onSubmit={submitHandler} className='search-box-form'>
      <Form.Control
        type='text'
        name='q'
        onChange={(e) => setKeyword(e.target.value)}
        value={keyword}
        placeholder='Search products'
        className='search-box-input'
      />
      <Button
        type='submit'
        variant='outline-light'
        className='search-box-button'
      >
        Search
      </Button>
    </Form>
  );
};

export default SearchBox;
