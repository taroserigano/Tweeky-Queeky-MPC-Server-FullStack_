import React, { useState, useEffect, useRef } from "react";
import { Form, Button, ListGroup } from "react-bootstrap";
import { useParams, useNavigate } from "react-router-dom";
import { FiSearch } from "react-icons/fi";
import axios from "axios";
import { BASE_URL } from "../constants";

const SearchBox = () => {
  const navigate = useNavigate();
  const { keyword: urlKeyword } = useParams();

  const [keyword, setKeyword] = useState(urlKeyword || "");
  const [debouncedKeyword, setDebouncedKeyword] = useState(keyword);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);

  // Click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedKeyword(keyword);
    }, 300);

    return () => {
      clearTimeout(timer);
    };
  }, [keyword]);

  // Fetch autocomplete suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (debouncedKeyword.length >= 2) {
        try {
          const { data } = await axios.get(
            `${BASE_URL}/api/products/autocomplete`,
            { params: { q: debouncedKeyword } }
          );
          setSuggestions(data);
          setShowSuggestions(true);
        } catch (error) {
          console.error("Error fetching suggestions:", error);
          setSuggestions([]);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };

    fetchSuggestions();
  }, [debouncedKeyword]);

  const submitHandler = (e) => {
    e.preventDefault();
    if (keyword) {
      navigate(`/search/${keyword.trim()}`);
      setShowSuggestions(false);
    } else {
      navigate("/");
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.type === "product") {
      navigate(`/product/${suggestion.id}`);
    } else {
      setKeyword(suggestion.text);
      navigate(`/search/${suggestion.text}`);
    }
    setShowSuggestions(false);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev < suggestions.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      handleSuggestionClick(suggestions[selectedIndex]);
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const getSuggestionIcon = (type) => {
    switch (type) {
      case "product":
        return "🛍️";
      case "brand":
        return "🏷️";
      case "category":
        return "📦";
      default:
        return "🔍";
    }
  };

  return (
    <div ref={searchRef} style={{ position: "relative" }}>
      <Form onSubmit={submitHandler} className="search-box-form">
        <Form.Control
          type="text"
          name="q"
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={handleKeyDown}
          value={keyword}
          placeholder="Search products, brands, categories..."
          className="search-box-input"
          autoComplete="off"
        />
        <Button type="submit" className="search-box-button">
          <FiSearch style={{ fontSize: "1.1rem" }} />
        </Button>
      </Form>

      {/* Autocomplete Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <ListGroup
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            zIndex: 1000,
            maxHeight: "400px",
            overflowY: "auto",
            marginTop: "4px",
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          }}
        >
          {suggestions.map((suggestion, index) => (
            <ListGroup.Item
              key={index}
              action
              onClick={() => handleSuggestionClick(suggestion)}
              style={{
                cursor: "pointer",
                backgroundColor:
                  selectedIndex === index ? "#f8f9fa" : "white",
                borderLeft: "none",
                borderRight: "none",
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span style={{ fontSize: "1.2rem" }}>
                {getSuggestionIcon(suggestion.type)}
              </span>
              <div>
                <div style={{ fontWeight: 500 }}>{suggestion.text}</div>
                <small style={{ color: "#6c757d", textTransform: "capitalize" }}>
                  {suggestion.type}
                </small>
              </div>
            </ListGroup.Item>
          ))}
        </ListGroup>
      )}
    </div>
  );
};

export default SearchBox;
