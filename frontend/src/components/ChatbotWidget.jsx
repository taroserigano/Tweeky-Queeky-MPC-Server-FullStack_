import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  FiMessageCircle,
  FiX,
  FiSend,
  FiMinimize2,
  FiShoppingCart,
  FiPlus,
  FiMinus,
} from "react-icons/fi";
import { BsRobot, BsStarFill, BsStarHalf, BsStar } from "react-icons/bs";
import ReactMarkdown from "react-markdown";
import { addToCart, removeFromCart, setCartItemQty } from "../slices/cartSlice";
import "./ChatbotWidget.css";

/* ── Unified endpoint: GPT + MCP + RAG all in one ── */
const ENDPOINT = "/api/agent/v2/chat";

/* ── Strip text-based product listings when product cards exist ── */
const stripProductListing = (text, hasCards) => {
  if (!hasCards || !text) return text;
  const lines = text.split("\n");
  const cleaned = [];
  for (const line of lines) {
    const t = line.trim();
    if (!t) continue;
    // Skip numbered lists: "1. Product Name ..."
    if (/^\d+\.\s+/.test(t)) continue;
    // Skip bullet lists: "• Product", "- Product", "* Product"
    if (/^[•\-*]\s+\S/.test(t)) continue;
    // Skip lines with price patterns: "$99.99"
    if (/\$\d+(\.\d{2})?/.test(t)) continue;
    // Skip lines with star/rating patterns: "⭐", "4.7/5"
    if (/[⭐★]/.test(t) || /\d\.\d\/5/.test(t)) continue;
    // Skip "Found X products" lines
    if (/found\s+\d+\s+product/i.test(t)) continue;
    // Skip recommendation headers
    if (/^(my\s+)?recommendations?:/i.test(t)) continue;
    if (/here\s+are\s+(some|the)\s+(picks|best|top|highest|great)/i.test(t))
      continue;
    // Skip "Top N rated" lines
    if (/^top\s+\d+\s+rated/i.test(t)) continue;
    // Skip separator lines
    if (t === "---") continue;
    cleaned.push(line);
  }
  const result = cleaned.join("\n").trim();
  return result || "Here are the products I found for you!";
};

/* ── Star rating ── */
const StarRating = ({ rating }) => {
  const stars = [];
  for (let i = 1; i <= 5; i++) {
    if (rating >= i) stars.push(<BsStarFill key={i} />);
    else if (rating >= i - 0.5) stars.push(<BsStarHalf key={i} />);
    else stars.push(<BsStar key={i} />);
  }
  return <span className="pc-stars">{stars}</span>;
};

/* ── Product Card (Amazon Rufus-style — flat list item) ── */
const ProductCard = ({ product, dispatch, navigate, closeChat }) => {
  const cartItem = useSelector((state) =>
    state.cart.cartItems.find((x) => x._id === product._id),
  );
  const qty = cartItem ? cartItem.qty : 0;
  const maxStock = product.countInStock || 0;

  const imgSrc =
    product.image && product.image !== "/images/sample.jpg"
      ? product.image
      : `https://ui-avatars.com/api/?name=${encodeURIComponent(product.name)}&background=f0f0f0&color=333&size=80&bold=true&length=2`;

  const handleAdd = () => {
    dispatch(
      addToCart({
        _id: product._id,
        name: product.name,
        price: product.price,
        image: product.image || "/images/sample.jpg",
        countInStock: maxStock,
        qty: 1,
      }),
    );
  };

  const handleIncrement = () => {
    if (qty < maxStock) {
      dispatch(setCartItemQty({ _id: product._id, qty: qty + 1 }));
    }
  };

  const handleDecrement = () => {
    if (qty > 1) {
      dispatch(setCartItemQty({ _id: product._id, qty: qty - 1 }));
    } else {
      dispatch(removeFromCart(product._id));
    }
  };

  return (
    <div className="pc-item">
      <div className="pc-row">
        <img
          className="pc-img"
          src={imgSrc}
          alt={product.name}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(product.name)}&background=f0f0f0&color=333&size=80&bold=true&length=2`;
          }}
        />
        <div className="pc-info">
          <div className="pc-name">{product.name}</div>
          <div className="pc-rating">
            <StarRating rating={product.rating} />
            <span className="pc-reviews">({product.numReviews})</span>
          </div>
          <div className="pc-price">${product.price?.toFixed(2)}</div>
        </div>
      </div>
      {qty === 0 ? (
        <button className="pc-add-btn" onClick={handleAdd} disabled={!maxStock}>
          <FiShoppingCart size={13} />
          {maxStock ? " Add to cart" : " Out of stock"}
        </button>
      ) : (
        <div className="pc-qty-stepper">
          <button className="pc-qty-btn" onClick={handleDecrement}>
            <FiMinus size={14} />
          </button>
          <span className="pc-qty-count">{qty}</span>
          <button
            className="pc-qty-btn"
            onClick={handleIncrement}
            disabled={qty >= maxStock}
          >
            <FiPlus size={14} />
          </button>
        </div>
      )}
      {product.description && (
        <div className="pc-desc">{product.description}</div>
      )}
      <a
        href={`/product/${product._id}`}
        className="pc-details-link"
        onClick={(e) => {
          e.preventDefault();
          navigate(`/product/${product._id}`);
          closeChat();
        }}
      >
        More details
      </a>
    </div>
  );
};

/* ── Intent → badge label & CSS class ── */
const INTENT_BADGES = {
  order_tracking: { label: "MCP", cls: "mcp" },
  knowledge: { label: "RAG", cls: "rag" },
  search: { label: "DB", cls: "db" },
  recommendation: { label: "AI", cls: "ai" },
  cart: { label: "CART", cls: "cart" },
  both: { label: "AI", cls: "ai" },
};

const ChatbotWidget = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [servicesHealth, setServicesHealth] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Hi! I'm your AI shopping assistant powered by GPT + MCP + RAG.\nI can search products, track orders, and answer store policy questions — all in one place!",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (messages[messages.length - 1]?.role === "assistant") {
      scrollToBottom();
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
      checkServicesHealth();
    }
  }, [isOpen, isMinimized]);

  const checkServicesHealth = async () => {
    try {
      const res = await fetch("/api/gateway/health");
      if (res.ok) {
        const data = await res.json();
        setServicesHealth(data);
      }
    } catch {
      setServicesHealth(null);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      const response = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: inputText }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to get response");
      }

      const data = await response.json();

      // Process cart actions — add items to Redux store
      if (data.cart_actions && data.cart_actions.length > 0) {
        data.cart_actions.forEach((item) => {
          dispatch(addToCart({ ...item, qty: item.qty || 1 }));
        });
      }

      const assistantMessage = {
        role: "assistant",
        content: stripProductListing(
          data.response || data.message || "I couldn't process that.",
          (data.product_cards || []).length > 0,
        ),
        intent: data.intent,
        agent: data.agent_used,
        productCards: data.product_cards || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting. Please try again later.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    setIsMinimized(false);
  };

  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  const quickActions = [
    "Show me wireless headphones",
    "What's the best laptop for work?",
    "Compare gaming chairs under $300",
    "Do you offer free shipping?",
  ];

  const handleQuickAction = (action) => {
    setInputText(action);
    inputRef.current?.focus();
  };

  /* Intent → badge helper */
  const getBadge = (intent) => {
    const b = INTENT_BADGES[intent];
    return b || { label: "AI", cls: "ai" };
  };

  /* Custom link renderer: internal links use React Router navigation */
  const ChatLink = useCallback(
    ({ href, children, ...props }) => {
      // Normalize: strip any domain the LLM may have prepended
      let cleanHref = href || "";
      try {
        const url = new URL(cleanHref, window.location.origin);
        if (url.origin !== window.location.origin) {
          // LLM added a fake domain like example.com — extract the path
          const match = cleanHref.match(
            /\/(product|order|add-to-cart)\/[a-f0-9]+/i,
          );
          if (match) {
            cleanHref = match[0];
            // Preserve query string for add-to-cart links
            const qIdx = (href || "").indexOf("?");
            if (qIdx !== -1) cleanHref += (href || "").slice(qIdx);
          }
        }
      } catch {
        // not a valid URL, use as-is
      }

      /* ── Add to Cart link (fallback for LLM-generated links) ── */
      if (cleanHref.startsWith("/add-to-cart/")) {
        const handleAddToCart = (e) => {
          e.preventDefault();
          try {
            const urlObj = new URL(cleanHref, window.location.origin);
            const pathParts = urlObj.pathname.split("/");
            const productId = pathParts[pathParts.length - 1];
            const params = urlObj.searchParams;
            dispatch(
              addToCart({
                _id: productId,
                name: params.get("name") || "Product",
                price: parseFloat(params.get("price")) || 0,
                image: params.get("image") || "/images/sample.jpg",
                countInStock: parseInt(params.get("countInStock")) || 0,
                qty: 1,
              }),
            );
          } catch (err) {
            console.error("Failed to add to cart:", err);
          }
        };
        return (
          <button className="chat-add-to-cart-btn" onClick={handleAddToCart}>
            🛒 Add to Cart
          </button>
        );
      }

      const isInternal =
        cleanHref.startsWith("/product/") ||
        cleanHref.startsWith("/order/") ||
        cleanHref === "/cart";

      if (isInternal) {
        return (
          <a
            href={cleanHref}
            onClick={(e) => {
              e.preventDefault();
              navigate(cleanHref);
              setIsOpen(false); // close chat to show the page
            }}
            className="chat-internal-link"
            {...props}
          >
            {children}
          </a>
        );
      }

      return (
        <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
          {children}
        </a>
      );
    },
    [navigate, dispatch],
  );

  /* Markdown component overrides for chat bubbles */
  const markdownComponents = { a: ChatLink };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          className="chatbot-button"
          onClick={toggleChat}
          aria-label="Open chat"
        >
          <FiMessageCircle size={24} />
          <span className="chatbot-badge">AI</span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className={`chatbot-window ${isMinimized ? "minimized" : ""}`}>
          {/* Header */}
          <div className="chatbot-header">
            <div className="chatbot-header-left">
              <div className="chatbot-avatar">
                <BsRobot size={20} />
              </div>
              <div className="chatbot-header-info">
                <h4>Shopping Assistant</h4>
                <span className="chatbot-status">
                  <span className="status-dot"></span>
                  GPT + MCP + RAG
                  {servicesHealth && (
                    <span
                      className={`mode-health-dot ${servicesHealth.all_healthy ? "healthy" : "unhealthy"}`}
                      title={
                        servicesHealth.all_healthy
                          ? "All services online"
                          : "Some services offline"
                      }
                    />
                  )}
                </span>
              </div>
            </div>
            <div className="chatbot-header-actions">
              <button
                onClick={toggleMinimize}
                className="chatbot-icon-btn"
                aria-label="Minimize"
              >
                <FiMinimize2 size={18} />
              </button>
              <button
                onClick={toggleChat}
                className="chatbot-icon-btn"
                aria-label="Close chat"
              >
                <FiX size={20} />
              </button>
            </div>
          </div>

          {/* Messages */}
          {!isMinimized && (
            <>
              <div className="chatbot-messages">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`chatbot-message ${msg.role === "user" ? "user" : "assistant"}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="message-avatar">
                        <BsRobot size={16} />
                      </div>
                    )}
                    <div className="message-content">
                      <div className="message-bubble">
                        <ReactMarkdown components={markdownComponents}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                      {/* Product Cards (Rufus-style vertical list) */}
                      {msg.productCards && msg.productCards.length > 0 && (
                        <div className="pc-list">
                          {msg.productCards.map((p) => (
                            <ProductCard
                              key={p._id}
                              product={p}
                              dispatch={dispatch}
                              navigate={navigate}
                              closeChat={() => setIsOpen(false)}
                            />
                          ))}
                        </div>
                      )}
                      {msg.intent && (
                        <div className="message-meta">
                          <span
                            className={`message-mode-badge ${getBadge(msg.intent).cls}`}
                          >
                            {getBadge(msg.intent).label}
                          </span>
                          {msg.agent && (
                            <span className="message-agent">
                              via {msg.agent}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="chatbot-message assistant">
                    <div className="message-avatar">
                      <BsRobot size={16} />
                    </div>
                    <div className="message-content">
                      <div className="message-bubble typing">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Quick Actions */}
              {messages.length <= 2 && (
                <div className="chatbot-quick-actions">
                  <p className="quick-actions-title">Try asking:</p>
                  <div className="quick-actions-grid">
                    {quickActions.map((action, index) => (
                      <button
                        key={index}
                        className="quick-action-btn"
                        onClick={() => handleQuickAction(action)}
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <div className="chatbot-input-container">
                <textarea
                  ref={inputRef}
                  className="chatbot-input"
                  placeholder="Ask me anything..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  rows={1}
                  disabled={isLoading}
                />
                <button
                  className="chatbot-send-btn"
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  aria-label="Send message"
                >
                  <FiSend size={18} />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default ChatbotWidget;
