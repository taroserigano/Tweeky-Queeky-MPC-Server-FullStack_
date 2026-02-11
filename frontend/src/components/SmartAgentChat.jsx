import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  FiSend,
  FiShoppingCart,
  FiCpu,
  FiPlus,
  FiCheck,
  FiStar,
  FiLoader,
  FiMessageCircle,
  FiRefreshCw,
  FiZap,
  FiTool,
  FiDatabase,
  FiSearch,
} from "react-icons/fi";
import { addToCart } from "../slices/cartSlice";
import {
  useAgentChat,
  useAgentStatus,
  QUICK_ACTIONS,
} from "../hooks/useAgentQueries";

/* ─────────────────────────────────────────────────────────────────────────────
   Styles
───────────────────────────────────────────────────────────────────────────── */
const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    minHeight: "600px",
    background: "#fff",
    borderRadius: "20px",
    border: "1px solid #e2e8f0",
    overflow: "hidden",
  },
  header: {
    padding: "16px 20px",
    background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  headerIcon: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    background: "rgba(255,255,255,0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
  },
  headerSubtitle: {
    margin: 0,
    fontSize: "12px",
    opacity: 0.8,
  },
  statusBadge: (connected) => ({
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    borderRadius: "20px",
    background: connected ? "rgba(255,255,255,0.2)" : "rgba(239,68,68,0.3)",
    fontSize: "12px",
    fontWeight: "500",
  }),
  statusDot: (connected) => ({
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: connected ? "#4ade80" : "#f87171",
  }),
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    background: "#f8fafc",
  },
  welcomeBox: {
    textAlign: "center",
    padding: "32px 20px",
    color: "#64748b",
  },
  welcomeIcon: {
    width: "64px",
    height: "64px",
    borderRadius: "20px",
    background: "linear-gradient(135deg, #10b981, #059669)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 16px",
    color: "#fff",
    fontSize: "28px",
  },
  welcomeTitle: {
    fontSize: "20px",
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: "8px",
  },
  welcomeText: {
    fontSize: "14px",
    lineHeight: "1.6",
    marginBottom: "24px",
    maxWidth: "400px",
    margin: "0 auto 24px",
  },
  capabilities: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    justifyContent: "center",
    marginBottom: "24px",
  },
  capBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 14px",
    borderRadius: "20px",
    background: "#fff",
    border: "1px solid #e2e8f0",
    fontSize: "12px",
    color: "#475569",
  },
  message: (isUser) => ({
    maxWidth: "85%",
    alignSelf: isUser ? "flex-end" : "flex-start",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  }),
  messageBubble: (isUser) => ({
    background: isUser ? "linear-gradient(135deg, #3b82f6, #2563eb)" : "#fff",
    color: isUser ? "#fff" : "#1e293b",
    padding: "14px 18px",
    borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    fontSize: "14px",
    lineHeight: "1.6",
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
    border: isUser ? "none" : "1px solid #e2e8f0",
  }),
  toolCalls: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
    marginTop: "4px",
  },
  toolBadge: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "4px 10px",
    borderRadius: "12px",
    background: "rgba(16, 185, 129, 0.1)",
    fontSize: "11px",
    color: "#059669",
    fontWeight: "500",
  },
  productCards: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: "12px",
    marginTop: "12px",
  },
  productCard: {
    background: "#fff",
    borderRadius: "12px",
    padding: "12px",
    border: "1px solid #e2e8f0",
    textDecoration: "none",
    color: "inherit",
    transition: "all 0.2s",
  },
  productImage: {
    width: "100%",
    height: "100px",
    objectFit: "cover",
    borderRadius: "8px",
    background: "#f1f5f9",
    marginBottom: "10px",
  },
  productName: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#1e293b",
    marginBottom: "4px",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  },
  productMeta: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "8px",
  },
  productPrice: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#10b981",
  },
  productRating: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "12px",
    color: "#f59e0b",
  },
  addBtn: (added) => ({
    width: "100%",
    marginTop: "8px",
    padding: "8px",
    border: "none",
    borderRadius: "8px",
    background: added
      ? "linear-gradient(135deg, #10b981, #059669)"
      : "linear-gradient(135deg, #3b82f6, #2563eb)",
    color: "#fff",
    fontSize: "12px",
    fontWeight: "500",
    cursor: added ? "default" : "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    transition: "all 0.2s",
  }),
  typing: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "12px 16px",
    background: "#fff",
    borderRadius: "18px",
    fontSize: "13px",
    color: "#64748b",
    border: "1px solid #e2e8f0",
    alignSelf: "flex-start",
  },
  quickActions: {
    padding: "12px 20px",
    background: "#fff",
    borderTop: "1px solid #f1f5f9",
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    justifyContent: "center",
  },
  quickBtn: {
    padding: "8px 14px",
    background: "#f1f5f9",
    border: "none",
    borderRadius: "20px",
    fontSize: "12px",
    color: "#475569",
    cursor: "pointer",
    transition: "all 0.2s",
    whiteSpace: "nowrap",
  },
  inputArea: {
    padding: "16px 20px",
    background: "#fff",
    borderTop: "1px solid #f1f5f9",
    display: "flex",
    gap: "12px",
    alignItems: "flex-end",
  },
  inputWrapper: {
    flex: 1,
    position: "relative",
  },
  input: {
    width: "100%",
    padding: "14px 18px",
    border: "2px solid #e2e8f0",
    borderRadius: "16px",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.2s",
    resize: "none",
    fontFamily: "inherit",
    minHeight: "52px",
    maxHeight: "120px",
  },
  sendBtn: (disabled) => ({
    padding: "14px 20px",
    background: disabled
      ? "#94a3b8"
      : "linear-gradient(135deg, #10b981, #059669)",
    color: "#fff",
    border: "none",
    borderRadius: "14px",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontWeight: "500",
    transition: "all 0.2s",
    height: "52px",
  }),
};

/* ─────────────────────────────────────────────────────────────────────────────
   Helper Components
───────────────────────────────────────────────────────────────────────────── */

const TypingIndicator = () => (
  <div style={styles.typing}>
    <FiLoader className="spin-animation" size={16} />
    <span>AI is thinking...</span>
  </div>
);

const ProductCard = ({ product, onAddToCart, isAdded }) => {
  const dispatch = useDispatch();

  const handleAdd = (e) => {
    e.preventDefault();
    if (!isAdded) {
      onAddToCart(product);
    }
  };

  return (
    <div style={styles.productCard}>
      <Link to={`/product/${product.id || product._id}`}>
        <img
          src={product.image || "/images/placeholder.jpg"}
          alt={product.name}
          style={styles.productImage}
          onError={(e) => {
            e.target.src = "/images/placeholder.jpg";
          }}
        />
        <div style={styles.productName}>{product.name}</div>
      </Link>
      <div style={styles.productMeta}>
        <span style={styles.productPrice}>${product.price?.toFixed(2)}</span>
        <span style={styles.productRating}>
          <FiStar size={12} />
          {product.rating?.toFixed(1) || "N/A"}
        </span>
      </div>
      <button style={styles.addBtn(isAdded)} onClick={handleAdd}>
        {isAdded ? (
          <>
            <FiCheck size={14} /> Added
          </>
        ) : (
          <>
            <FiPlus size={14} /> Add to Cart
          </>
        )}
      </button>
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────────────────────
   Main Component
───────────────────────────────────────────────────────────────────────────── */

const SmartAgentChat = ({ height = "600px" }) => {
  const dispatch = useDispatch();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [addedProducts, setAddedProducts] = useState(new Set());
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Queries
  const { data: agentStatus } = useAgentStatus();
  const chatMutation = useAgentChat();

  const isConnected = agentStatus?.status === "operational";
  const isLoading = chatMutation.isPending;

  // Auto-scroll when messages change or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Strip ALL product listings from text when we have product cards to show
  const stripProductListing = (text, hasProducts) => {
    if (!hasProducts || !text) return text;

    // Split into lines and aggressively filter out any product-related lines
    const lines = text.split("\n");
    const cleaned = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // Skip numbered lists: "1. Product Name ...", "2. Bose ..."
      if (/^\d+\.\s+/.test(trimmed)) continue;

      // Skip bullet lists: "• Product", "- Product", "* Product"
      if (/^[•\-\*]\s+\S/.test(trimmed)) continue;

      // Skip lines with price patterns: "$99.99", "— $", "($"
      if (/\$\d+(\.\d{2})?/.test(trimmed)) continue;

      // Skip lines with star/rating patterns: "⭐", "(4.7/5)", "4.6/5"
      if (/[⭐★]/.test(trimmed) || /\d\.\d\/5/.test(trimmed)) continue;

      // Skip "Found X products" lines
      if (/found\s+\d+\s+product/i.test(trimmed)) continue;

      // Skip "My Recommendations:" or "Here are some picks" headers
      if (/^(my\s+)?recommendations?:/i.test(trimmed)) continue;
      if (
        /here\s+are\s+(some|the)\s+(picks|best|top|highest|great)/i.test(
          trimmed,
        )
      )
        continue;

      // Skip "Top N rated products" lines
      if (/^top\s+\d+\s+rated/i.test(trimmed)) continue;

      cleaned.push(line);
    }

    const result = cleaned.join("\n").trim();
    // If everything was stripped, return a generic message
    return result || "Here are the products I found for you!";
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const result = await chatMutation.mutateAsync({
        message: userMessage,
        threadId,
      });

      console.log("[SmartAgentChat] Response:", result);

      // Store thread ID for conversation continuity
      if (result?.thread_id) {
        setThreadId(result.thread_id);
      }

      // Get the message content directly
      const messageContent =
        result?.message || result?.reply || "No message in response";

      // Use structured products from backend (not regex-parsed from text)
      const products = result?.products || [];

      // Strip text-based product listing if we have structured product cards
      const displayContent = stripProductListing(
        messageContent,
        products.length > 0,
      );

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: displayContent,
          toolCalls: result?.tool_calls || [],
          products: products,
        },
      ]);
    } catch (error) {
      console.error(
        "[SmartAgentChat] Error:",
        error?.response?.data || error?.message || error,
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error?.response?.data?.detail || error.message || "Something went wrong"}. Please try again.`,
          isError: true,
        },
      ]);
    }
  };

  const handleQuickAction = (action) => {
    setInput(action.query);
    inputRef.current?.focus();
  };

  const handleAddToCart = (product) => {
    const cartProduct = {
      ...product,
      _id: product.id || product._id,
      countInStock: product.count_in_stock || product.countInStock || 10,
      qty: 1,
    };
    dispatch(addToCart(cartProduct));
    setAddedProducts((prev) => new Set([...prev, product.id || product._id]));
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setThreadId(null);
  };

  return (
    <div style={{ ...styles.container, height }}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.headerIcon}>
            <FiCpu size={20} />
          </div>
          <div>
            <h3 style={styles.headerTitle}>Smart Shopping Agent</h3>
            <p style={styles.headerSubtitle}>Powered by LangGraph + RAG</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {threadId && (
            <button
              onClick={handleNewChat}
              style={{
                ...styles.statusBadge(true),
                cursor: "pointer",
                border: "none",
              }}
            >
              <FiRefreshCw size={14} />
              New Chat
            </button>
          )}
          <div style={styles.statusBadge(isConnected)}>
            <div style={styles.statusDot(isConnected)} />
            {isConnected ? "Online" : "Offline"}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 ? (
          <div style={styles.welcomeBox}>
            <div style={styles.welcomeIcon}>
              <FiZap />
            </div>
            <h2 style={styles.welcomeTitle}>
              Hi! I'm your AI Shopping Assistant
            </h2>
            <p style={styles.welcomeText}>
              I can help you find products, compare options, build shopping
              carts within your budget, and answer questions about any product
              in our catalog.
            </p>
            <div style={styles.capabilities}>
              <span style={styles.capBadge}>
                <FiSearch size={14} /> Semantic Search
              </span>
              <span style={styles.capBadge}>
                <FiDatabase size={14} /> RAG-Powered
              </span>
              <span style={styles.capBadge}>
                <FiTool size={14} /> Tool Calling
              </span>
              <span style={styles.capBadge}>
                <FiMessageCircle size={14} /> Context Memory
              </span>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} style={styles.message(msg.role === "user")}>
              <div style={styles.messageBubble(msg.role === "user")}>
                {msg.content}
              </div>
              {msg.toolCalls?.length > 0 && (
                <div style={styles.toolCalls}>
                  {msg.toolCalls.map((tool, i) => (
                    <span key={i} style={styles.toolBadge}>
                      <FiTool size={10} />
                      {tool.name || tool}
                    </span>
                  ))}
                </div>
              )}
              {msg.products?.length > 0 && (
                <div style={styles.productCards}>
                  {msg.products.slice(0, 4).map((product, i) => (
                    <ProductCard
                      key={i}
                      product={product}
                      onAddToCart={handleAddToCart}
                      isAdded={addedProducts.has(product.id || product._id)}
                    />
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {messages.length === 0 && (
        <div style={styles.quickActions}>
          {QUICK_ACTIONS.slice(0, 4).map((action) => (
            <button
              key={action.id}
              style={styles.quickBtn}
              onClick={() => handleQuickAction(action)}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={styles.inputArea}>
        <div style={styles.inputWrapper}>
          <textarea
            ref={inputRef}
            style={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about products..."
            rows={1}
            disabled={isLoading}
          />
        </div>
        <button
          style={styles.sendBtn(isLoading || !input.trim())}
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? <FiLoader className="spin-animation" /> : <FiSend />}
        </button>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin-animation {
          animation: spin 1s linear infinite;
        }
        ${styles.input}:focus {
          border-color: #10b981;
        }
        ${styles.quickBtn}:hover {
          background: #e2e8f0;
          transform: translateY(-1px);
        }
        ${styles.productCard}:hover {
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};

export default SmartAgentChat;
