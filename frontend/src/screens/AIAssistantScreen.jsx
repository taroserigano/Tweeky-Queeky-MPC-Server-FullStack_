import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useDispatch } from "react-redux";
import {
  FiMessageSquare,
  FiSend,
  FiShoppingCart,
  FiSearch,
  FiTrendingUp,
  FiPackage,
  FiBarChart2,
  FiCpu,
  FiZap,
  FiBox,
  FiPlus,
  FiCheck,
  FiStar,
  FiDollarSign,
} from "react-icons/fi";
import { addToCart } from "../slices/cartSlice";
import {
  useCatalogStats,
  useCategoryPriceSummary,
  useTopProducts,
  useTopReviewedProducts,
  useProductSearch,
  useReviewSentiment,
} from "../hooks/useMCPQueries";

/* ─────────────────────────────────────────────────────────────────────────────
   Styles
───────────────────────────────────────────────────────────────────────────── */
const styles = {
  container: {
    minHeight: "calc(100vh - 120px)",
    background: "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
    padding: "24px 16px",
  },
  inner: {
    maxWidth: "1400px",
    margin: "0 auto",
  },
  header: {
    textAlign: "center",
    marginBottom: "32px",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
    color: "#fff",
    padding: "6px 14px",
    borderRadius: "50px",
    fontSize: "12px",
    fontWeight: "600",
    marginBottom: "12px",
  },
  title: {
    fontSize: "32px",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "8px",
  },
  subtitle: {
    fontSize: "16px",
    color: "#64748b",
    maxWidth: "600px",
    margin: "0 auto",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "24px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "16px",
    marginBottom: "24px",
  },
  statCard: {
    background: "#fff",
    borderRadius: "16px",
    padding: "20px",
    border: "1px solid #e2e8f0",
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },
  statIcon: (color) => ({
    width: "48px",
    height: "48px",
    borderRadius: "12px",
    background: color,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: "20px",
  }),
  statValue: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#1e293b",
  },
  statLabel: {
    fontSize: "13px",
    color: "#64748b",
  },
  chatSection: {
    background: "#fff",
    borderRadius: "20px",
    border: "1px solid #e2e8f0",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    height: "600px",
  },
  chatHeader: {
    padding: "20px 24px",
    borderBottom: "1px solid #f1f5f9",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
    color: "#fff",
  },
  chatTitle: {
    fontSize: "18px",
    fontWeight: "600",
    margin: 0,
  },
  chatMessages: {
    flex: 1,
    overflow: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  message: (isUser) => ({
    maxWidth: "80%",
    alignSelf: isUser ? "flex-end" : "flex-start",
    background: isUser
      ? "linear-gradient(135deg, #3b82f6, #2563eb)"
      : "#f1f5f9",
    color: isUser ? "#fff" : "#1e293b",
    padding: "14px 18px",
    borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    fontSize: "14px",
    lineHeight: "1.5",
  }),
  chatInput: {
    padding: "16px 20px",
    borderTop: "1px solid #f1f5f9",
    display: "flex",
    gap: "12px",
  },
  input: {
    flex: 1,
    padding: "14px 18px",
    border: "2px solid #e2e8f0",
    borderRadius: "12px",
    fontSize: "14px",
    outline: "none",
    transition: "all 0.2s",
  },
  sendBtn: {
    padding: "14px 20px",
    background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
    color: "#fff",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontWeight: "500",
    transition: "all 0.2s",
  },
  quickActions: {
    padding: "16px 20px",
    borderTop: "1px solid #f1f5f9",
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  quickBtn: {
    padding: "8px 14px",
    background: "#f1f5f9",
    border: "none",
    borderRadius: "20px",
    fontSize: "12px",
    color: "#475569",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "all 0.2s",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  card: {
    background: "#fff",
    borderRadius: "16px",
    border: "1px solid #e2e8f0",
    overflow: "hidden",
  },
  cardHeader: {
    padding: "16px 20px",
    borderBottom: "1px solid #f1f5f9",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  cardIcon: (color) => ({
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    background: color,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: "14px",
  }),
  cardTitle: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#1e293b",
    margin: 0,
  },
  cardBody: {
    padding: "16px 20px",
  },
  topProduct: {
    display: "flex",
    gap: "12px",
    padding: "12px 0",
    borderBottom: "1px solid #f1f5f9",
    alignItems: "center",
  },
  productImage: {
    width: "50px",
    height: "50px",
    borderRadius: "10px",
    objectFit: "cover",
    background: "#f8fafc",
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#1e293b",
    textDecoration: "none",
    display: "-webkit-box",
    WebkitLineClamp: 1,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  },
  productMeta: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "4px",
  },
  rating: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "12px",
    color: "#f59e0b",
  },
  price: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#10b981",
  },
  sentimentBar: {
    display: "flex",
    height: "8px",
    borderRadius: "4px",
    overflow: "hidden",
    marginTop: "12px",
  },
  sentimentSegment: (color, width) => ({
    background: color,
    width: `${width}%`,
  }),
  sentimentLegend: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "8px",
    fontSize: "12px",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: "#64748b",
  },
  legendDot: (color) => ({
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: color,
  }),
  categoryItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 0",
    borderBottom: "1px solid #f1f5f9",
  },
  categoryName: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#1e293b",
  },
  categoryStats: {
    textAlign: "right",
  },
  categoryCount: {
    fontSize: "12px",
    color: "#64748b",
  },
  categoryAvg: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#3b82f6",
  },
  recommendedProduct: {
    display: "flex",
    gap: "12px",
    padding: "12px",
    background: "#f8fafc",
    borderRadius: "12px",
    marginBottom: "12px",
    alignItems: "center",
  },
  addBtn: {
    padding: "8px 12px",
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "12px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  addedBtn: {
    padding: "8px 12px",
    background: "#10b981",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "12px",
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  toolsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "8px",
    marginBottom: "16px",
  },
  toolBtn: {
    padding: "12px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    fontSize: "12px",
    color: "#475569",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "6px",
    transition: "all 0.2s",
  },
  toolInputRow: {
    display: "flex",
    gap: "8px",
  },
  toolInput: {
    flex: 1,
    padding: "10px 12px",
    border: "1px solid #e2e8f0",
    borderRadius: "10px",
    fontSize: "12px",
  },
  toolActionBtn: {
    padding: "10px 12px",
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: "10px",
    fontSize: "12px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  alert: {
    background: "#fff7ed",
    border: "1px solid #fed7aa",
    color: "#9a3412",
    borderRadius: "12px",
    padding: "12px 16px",
    marginBottom: "20px",
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
  },
  alertTitle: {
    fontSize: "14px",
    fontWeight: "600",
    marginBottom: "2px",
  },
  alertText: {
    fontSize: "12px",
    color: "#9a3412",
    margin: 0,
  },
  retryBtn: {
    marginLeft: "auto",
    background: "#fff",
    border: "1px solid #fed7aa",
    color: "#9a3412",
    borderRadius: "8px",
    padding: "6px 10px",
    fontSize: "12px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
};

const responsiveStyles = `
  @media (min-width: 1024px) {
    .ai-grid {
      grid-template-columns: 1fr 380px !important;
    }
  }
`;

/* ─────────────────────────────────────────────────────────────────────────────
   Component
───────────────────────────────────────────────────────────────────────────── */
const AIAssistantScreen = () => {
  const dispatch = useDispatch();
  const messagesEndRef = useRef(null);
  const [input, setInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Hi! I can answer using real catalog data only (no AI guesses). Use the tools below to search, view top rated products, and get catalog insights.",
    },
  ]);
  const [addedProducts, setAddedProducts] = useState(new Set());

  // Data hooks
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsIsError,
    error: statsErrorData,
    refetch: refetchStats,
  } = useCatalogStats();
  const {
    data: categories,
    isError: categoriesIsError,
    error: categoriesErrorData,
    refetch: refetchCategories,
  } = useCategoryPriceSummary();
  const {
    data: topProducts,
    isError: topProductsIsError,
    error: topProductsErrorData,
    refetch: refetchTopProducts,
  } = useTopProducts(5);
  useTopReviewedProducts(3, { enabled: false });
  const {
    data: sentiment,
    isError: sentimentIsError,
    error: sentimentErrorData,
    refetch: refetchSentiment,
  } = useReviewSentiment();
  const {
    data: searchResults,
    refetch: refetchSearch,
    isFetching: isSearching,
  } = useProductSearch(searchQuery, 6, { enabled: false });

  const getErrorMessage = (err, fallback = "Service unavailable") => {
    return (
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      fallback
    );
  };

  const getFirstErrorMessage = (...errors) => {
    for (const err of errors) {
      if (err) {
        return getErrorMessage(err);
      }
    }
    return null;
  };

  const aiModelLabel = "Catalog Tools";
  const readOnlyError =
    statsIsError || categoriesIsError || topProductsIsError || sentimentIsError;
  const readOnlyErrorMessage = getFirstErrorMessage(
    statsErrorData,
    categoriesErrorData,
    topProductsErrorData,
    sentimentErrorData,
  );

  // Auto-scroll when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    if (/top reviewed|top-rated|best reviewed|top rated/i.test(userMessage)) {
      const result = await refetchTopProducts();
      const products = (result?.data || topProducts || []).slice(0, 3);
      if (products.length > 0) {
        const list = products
          .map((p, idx) => `${idx + 1}. ${p.name} (${p.brand}) - $${p.price}`)
          .join("\n");
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Here are the top rated products right now:\n\n${list}`,
            products,
          },
        ]);
        return;
      }
    }

    if (/search:/i.test(userMessage)) {
      const query = userMessage.split(":").slice(1).join(":").trim();
      if (query) {
        setSearchQuery(query);
        const result = await refetchSearch();
        const products = result?.data || [];
        if (products.length > 0) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `Found ${products.length} products for "${query}":`,
              products,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: `No results for "${query}".` },
          ]);
        }
        return;
      }
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content:
          'I only use catalog tools. Try: "List 3 top rated products" or "Search: wireless headphones".',
      },
    ]);
  };

  const handleQuickAction = async (action) => {
    setMessages((prev) => [...prev, { role: "user", content: action }]);

    if (/top reviewed|top-rated|best reviewed|top rated/i.test(action)) {
      const result = await refetchTopProducts();
      const products = (result?.data || topProducts || []).slice(0, 3);
      if (products.length > 0) {
        const list = products
          .map((p, idx) => `${idx + 1}. ${p.name} (${p.brand}) - $${p.price}`)
          .join("\n");
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Here are the top rated products right now:\n\n${list}`,
            products,
          },
        ]);
        return;
      }
    }

    if (action.toLowerCase().startsWith("search:")) {
      const query = action.split(":").slice(1).join(":").trim();
      if (query) {
        setSearchQuery(query);
        const result = await refetchSearch();
        const products = result?.data || [];
        if (products.length > 0) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `Found ${products.length} products for "${query}":`,
              products,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: `No results for "${query}".` },
          ]);
        }
        return;
      }
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content:
          'This assistant is limited to catalog tools. Try: "List 3 top rated products" or "Search: wireless headphones".',
      },
    ]);
  };

  const handleAddToCart = (product) => {
    dispatch(addToCart({ ...product, qty: 1 }));
    setAddedProducts((prev) => new Set([...prev, product.id]));
  };

  const runToolAction = (tool) => {
    switch (tool) {
      case "search":
        return handleQuickAction("Search: wireless headphones");
      case "recommend":
        return handleQuickAction("List 3 top rated products");
      case "compare":
        return handleQuickAction("Search: office chairs");
      case "cart":
        return handleQuickAction("Search: home office");
      case "top-rated":
        return handleQuickAction("List 3 top rated products");
      default:
        return null;
    }
  };

  const sentimentTotal = sentiment?.total_reviews || 1;
  const posPercent = ((sentiment?.positive || 0) / sentimentTotal) * 100;
  const neuPercent = ((sentiment?.neutral || 0) / sentimentTotal) * 100;
  const negPercent = ((sentiment?.negative || 0) / sentimentTotal) * 100;

  return (
    <>
      <style>{responsiveStyles}</style>
      <div style={styles.container}>
        <div style={styles.inner}>
          {/* Header */}
          <header style={styles.header}>
            <span style={styles.badge}>
              <FiCpu size={14} />
              AI-Powered
            </span>
            <h1 style={styles.title}>Shopping Assistant</h1>
            <p style={styles.subtitle}>
              Ask me anything about our products! I can help you find items,
              compare products, build carts within budget, and more.
            </p>
          </header>

          {readOnlyError && (
            <div style={styles.alert}>
              <FiZap />
              <div>
                <div style={styles.alertTitle}>MCP API unavailable</div>
                <p style={styles.alertText}>
                  {readOnlyErrorMessage || "Unable to reach the MCP API."}
                </p>
              </div>
              <button
                style={styles.retryBtn}
                onClick={() => {
                  refetchStats();
                  refetchCategories();
                  refetchTopProducts();
                  refetchSentiment();
                }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Stats */}
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statIcon("#3b82f6")}>
                <FiPackage />
              </div>
              <div>
                <div style={styles.statValue}>
                  {statsLoading ? "..." : stats?.total_products || 0}
                </div>
                <div style={styles.statLabel}>Products</div>
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statIcon("#8b5cf6")}>
                <FiMessageSquare />
              </div>
              <div>
                <div style={styles.statValue}>
                  {statsLoading ? "..." : stats?.total_reviews || 0}
                </div>
                <div style={styles.statLabel}>Reviews</div>
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statIcon("#10b981")}>
                <FiBarChart2 />
              </div>
              <div>
                <div style={styles.statValue}>
                  {Object.keys(stats?.categories || {}).length}
                </div>
                <div style={styles.statLabel}>Categories</div>
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statIcon("#f59e0b")}>
                <FiZap />
              </div>
              <div>
                <div style={styles.statValue}>{aiModelLabel}</div>
                <div style={styles.statLabel}>AI Model</div>
              </div>
            </div>
          </div>

          {/* Main Grid */}
          <div style={styles.grid} className="ai-grid">
            {/* Chat Section */}
            <div style={styles.chatSection}>
              <div style={styles.chatHeader}>
                <FiCpu size={24} />
                <h2 style={styles.chatTitle}>AI Chat</h2>
              </div>

              <div style={styles.chatMessages}>
                {messages.map((msg, index) => (
                  <div key={index}>
                    <div style={styles.message(msg.role === "user")}>
                      {msg.content}
                    </div>
                    {msg.products && (
                      <div style={{ marginTop: "12px", marginLeft: "8px" }}>
                        {msg.products.map((product) => (
                          <div
                            key={product.id}
                            style={styles.recommendedProduct}
                          >
                            <img
                              src={product.image}
                              alt={product.name}
                              style={styles.productImage}
                            />
                            <div style={styles.productInfo}>
                              <Link
                                to={`/product/${product.id}`}
                                style={styles.productName}
                              >
                                {product.name}
                              </Link>
                              <div style={styles.productMeta}>
                                <span style={styles.price}>
                                  ${product.price}
                                </span>
                                <span style={styles.rating}>
                                  <FiStar size={10} fill="#f59e0b" />
                                  {product.rating}
                                </span>
                              </div>
                            </div>
                            {addedProducts.has(product.id) ? (
                              <button style={styles.addedBtn}>
                                <FiCheck size={12} /> Added
                              </button>
                            ) : (
                              <button
                                style={styles.addBtn}
                                onClick={() => handleAddToCart(product)}
                              >
                                <FiPlus size={12} /> Add
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {msg.cartItems && (
                      <div style={{ marginTop: "12px", marginLeft: "8px" }}>
                        {msg.cartItems.map((item) => (
                          <div key={item.id} style={styles.recommendedProduct}>
                            <img
                              src={item.image}
                              alt={item.name}
                              style={styles.productImage}
                            />
                            <div style={styles.productInfo}>
                              <Link
                                to={`/product/${item.id}`}
                                style={styles.productName}
                              >
                                {item.name}
                              </Link>
                              <div style={styles.productMeta}>
                                <span style={styles.price}>
                                  ${item.price} × {item.qty}
                                </span>
                              </div>
                            </div>
                            {addedProducts.has(item.id) ? (
                              <button style={styles.addedBtn}>
                                <FiCheck size={12} /> Added
                              </button>
                            ) : (
                              <button
                                style={styles.addBtn}
                                onClick={() =>
                                  handleAddToCart({ ...item, qty: item.qty })
                                }
                              >
                                <FiPlus size={12} /> Add
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {isSearching && (
                  <div style={styles.message(false)}>Searching...</div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div style={styles.quickActions}>
                <button
                  style={styles.quickBtn}
                  onClick={() => handleQuickAction("List 3 top rated products")}
                >
                  <FiTrendingUp size={12} /> Top rated
                </button>
                <button
                  style={styles.quickBtn}
                  onClick={() => handleQuickAction("List 3 top rated products")}
                >
                  <FiStar size={12} /> Top rated
                </button>
                <button
                  style={styles.quickBtn}
                  onClick={() => handleQuickAction("Search: gaming")}
                >
                  <FiSearch size={12} /> Gaming gear
                </button>
                <button
                  style={styles.quickBtn}
                  onClick={() => handleQuickAction("Search: home office")}
                >
                  <FiShoppingCart size={12} /> Office setup
                </button>
                <button
                  style={styles.quickBtn}
                  onClick={() => handleQuickAction("Search: electronics")}
                >
                  <FiBox size={12} /> Electronics
                </button>
              </div>

              <div style={styles.chatInput}>
                <input
                  type="text"
                  style={styles.input}
                  placeholder="Type: Search: headphones or List 3 top rated products"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSend()}
                />
                <button
                  style={styles.sendBtn}
                  onClick={handleSend}
                  disabled={isSearching}
                >
                  <FiSend size={16} />
                  Send
                </button>
              </div>
            </div>

            {/* Sidebar */}
            <div style={styles.sidebar}>
              {/* Top Products */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div style={styles.cardIcon("#f59e0b")}>
                    <FiTrendingUp />
                  </div>
                  <h3 style={styles.cardTitle}>Top Rated Products</h3>
                </div>
                <div style={styles.cardBody}>
                  {topProducts?.map((product, index) => (
                    <div
                      key={product.id}
                      style={{
                        ...styles.topProduct,
                        borderBottom:
                          index === topProducts.length - 1 ? "none" : undefined,
                      }}
                    >
                      <img
                        src={product.image}
                        alt={product.name}
                        style={styles.productImage}
                      />
                      <div style={styles.productInfo}>
                        <Link
                          to={`/product/${product.id}`}
                          style={styles.productName}
                        >
                          {product.name}
                        </Link>
                        <div style={styles.productMeta}>
                          <span style={styles.rating}>
                            <FiStar size={10} fill="#f59e0b" />
                            {product.rating}
                          </span>
                          <span style={styles.price}>${product.price}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sentiment Analysis */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div style={styles.cardIcon("#8b5cf6")}>
                    <FiBarChart2 />
                  </div>
                  <h3 style={styles.cardTitle}>Review Sentiment</h3>
                </div>
                <div style={styles.cardBody}>
                  <div style={styles.sentimentBar}>
                    <div
                      style={styles.sentimentSegment("#10b981", posPercent)}
                    />
                    <div
                      style={styles.sentimentSegment("#94a3b8", neuPercent)}
                    />
                    <div
                      style={styles.sentimentSegment("#ef4444", negPercent)}
                    />
                  </div>
                  <div style={styles.sentimentLegend}>
                    <div style={styles.legendItem}>
                      <div style={styles.legendDot("#10b981")} />
                      Positive ({sentiment?.positive || 0})
                    </div>
                    <div style={styles.legendItem}>
                      <div style={styles.legendDot("#94a3b8")} />
                      Neutral ({sentiment?.neutral || 0})
                    </div>
                    <div style={styles.legendItem}>
                      <div style={styles.legendDot("#ef4444")} />
                      Negative ({sentiment?.negative || 0})
                    </div>
                  </div>
                </div>
              </div>

              {/* Categories */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div style={styles.cardIcon("#3b82f6")}>
                    <FiBox />
                  </div>
                  <h3 style={styles.cardTitle}>Categories</h3>
                </div>
                <div style={styles.cardBody}>
                  {categories?.slice(0, 5).map((cat, index) => (
                    <div
                      key={cat.category}
                      style={{
                        ...styles.categoryItem,
                        borderBottom:
                          index === Math.min(4, categories.length - 1)
                            ? "none"
                            : undefined,
                      }}
                    >
                      <span style={styles.categoryName}>{cat.category}</span>
                      <div style={styles.categoryStats}>
                        <div style={styles.categoryCount}>
                          {cat.count} products
                        </div>
                        <div style={styles.categoryAvg}>
                          <FiDollarSign size={12} />
                          {cat.avg_price} avg
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* MCP Info */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div style={styles.cardIcon("#10b981")}>
                    <FiCpu />
                  </div>
                  <h3 style={styles.cardTitle}>MCP Tools</h3>
                </div>
                <div style={styles.cardBody}>
                  <div style={styles.toolsGrid}>
                    <button
                      type="button"
                      style={styles.toolBtn}
                      onClick={() => runToolAction("search")}
                    >
                      <FiSearch size={16} />
                      Search
                    </button>
                    <button
                      type="button"
                      style={styles.toolBtn}
                      onClick={() => runToolAction("top-rated")}
                    >
                      <FiStar size={16} />
                      Top Rated
                    </button>
                    <button
                      type="button"
                      style={styles.toolBtn}
                      onClick={() => runToolAction("recommend")}
                    >
                      <FiTrendingUp size={16} />
                      Top Rated
                    </button>
                    <button
                      type="button"
                      style={styles.toolBtn}
                      onClick={() => runToolAction("compare")}
                    >
                      <FiBarChart2 size={16} />
                      Search
                    </button>
                    <button
                      type="button"
                      style={styles.toolBtn}
                      onClick={() => runToolAction("cart")}
                    >
                      <FiShoppingCart size={16} />
                      Search
                    </button>
                  </div>
                  <div style={styles.toolInputRow}>
                    <input
                      type="text"
                      style={styles.toolInput}
                      placeholder="Search products..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button
                      type="button"
                      style={styles.toolActionBtn}
                      onClick={() =>
                        handleQuickAction(`Search: ${searchQuery}`)
                      }
                      disabled={!searchQuery}
                    >
                      Search
                    </button>
                  </div>
                  <p
                    style={{
                      fontSize: "12px",
                      color: "#64748b",
                      margin: 0,
                      textAlign: "center",
                    }}
                  >
                    Tool-only mode (no AI guesses)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AIAssistantScreen;
