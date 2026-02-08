import { useState } from "react";
import { Link } from "react-router-dom";
import {
  FiBarChart2,
  FiBox,
  FiDollarSign,
  FiAlertTriangle,
  FiTrendingUp,
  FiTrendingDown,
  FiRefreshCw,
  FiDatabase,
  FiCpu,
  FiPackage,
  FiStar,
  FiShoppingBag,
  FiUsers,
  FiActivity,
  FiPieChart,
  FiLayers,
} from "react-icons/fi";
import {
  useCatalogStats,
  useCategoryPriceSummary,
  useTopProducts,
  useReviewSentiment,
} from "../hooks/useMCPQueries";
import { useRAGStatus } from "../hooks/useAgentQueries";

/* ─────────────────────────────────────────────────────────────────────────────
   Styles
───────────────────────────────────────────────────────────────────────────── */
const styles = {
  container: {
    minHeight: "calc(100vh - 120px)",
    background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
    padding: "24px",
    color: "#fff",
  },
  inner: {
    maxWidth: "1400px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "32px",
  },
  title: {
    fontSize: "28px",
    fontWeight: "700",
    marginBottom: "8px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  subtitle: {
    fontSize: "14px",
    color: "#94a3b8",
  },
  refreshBtn: {
    padding: "10px 18px",
    background: "rgba(255,255,255,0.1)",
    border: "1px solid rgba(255,255,255,0.2)",
    borderRadius: "10px",
    color: "#fff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "14px",
    transition: "all 0.2s",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
    gap: "20px",
    marginBottom: "32px",
  },
  statCard: {
    background: "rgba(255,255,255,0.05)",
    backdropFilter: "blur(10px)",
    borderRadius: "16px",
    padding: "24px",
    border: "1px solid rgba(255,255,255,0.1)",
  },
  statHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "16px",
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
  statTrend: (positive) => ({
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: "500",
    background: positive ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)",
    color: positive ? "#10b981" : "#ef4444",
  }),
  statValue: {
    fontSize: "32px",
    fontWeight: "700",
    marginBottom: "4px",
  },
  statLabel: {
    fontSize: "14px",
    color: "#94a3b8",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "24px",
    marginBottom: "24px",
  },
  card: {
    background: "rgba(255,255,255,0.05)",
    backdropFilter: "blur(10px)",
    borderRadius: "16px",
    border: "1px solid rgba(255,255,255,0.1)",
    overflow: "hidden",
  },
  cardHeader: {
    padding: "20px 24px",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardTitle: {
    fontSize: "16px",
    fontWeight: "600",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    margin: 0,
  },
  cardBody: {
    padding: "20px 24px",
  },
  categoryRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 0",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
  },
  categoryName: {
    fontSize: "14px",
    fontWeight: "500",
  },
  categoryStats: {
    display: "flex",
    gap: "16px",
    fontSize: "13px",
    color: "#94a3b8",
  },
  sentimentBar: {
    display: "flex",
    height: "24px",
    borderRadius: "12px",
    overflow: "hidden",
    marginBottom: "16px",
  },
  sentimentSegment: (color, width) => ({
    background: color,
    width: `${width}%`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "11px",
    fontWeight: "600",
    transition: "width 0.3s",
  }),
  sentimentLegend: {
    display: "flex",
    justifyContent: "space-around",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
  },
  legendDot: (color) => ({
    width: "12px",
    height: "12px",
    borderRadius: "4px",
    background: color,
  }),
  topProduct: {
    display: "flex",
    gap: "16px",
    padding: "16px 0",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
    alignItems: "center",
  },
  productRank: {
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    background: "linear-gradient(135deg, #f59e0b, #d97706)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    fontWeight: "700",
  },
  productImage: {
    width: "56px",
    height: "56px",
    borderRadius: "10px",
    objectFit: "cover",
    background: "rgba(255,255,255,0.1)",
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    fontSize: "14px",
    fontWeight: "500",
    marginBottom: "4px",
    color: "#fff",
    textDecoration: "none",
    display: "block",
  },
  productMeta: {
    display: "flex",
    gap: "12px",
    fontSize: "12px",
    color: "#94a3b8",
  },
  statusGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "16px",
  },
  statusCard: (color) => ({
    padding: "16px",
    borderRadius: "12px",
    background: `linear-gradient(135deg, ${color}20, ${color}10)`,
    border: `1px solid ${color}40`,
    textAlign: "center",
  }),
  statusValue: {
    fontSize: "18px",
    fontWeight: "700",
    marginBottom: "4px",
  },
  statusLabel: {
    fontSize: "12px",
    color: "#94a3b8",
  },
  fullWidth: {
    gridColumn: "1 / -1",
  },
  loadingState: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px",
    color: "#94a3b8",
    gap: "12px",
  },
  errorState: {
    padding: "20px",
    borderRadius: "12px",
    background: "rgba(239,68,68,0.1)",
    border: "1px solid rgba(239,68,68,0.3)",
    color: "#fca5a5",
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
};

const responsiveStyles = `
  @media (max-width: 768px) {
    .analytics-grid {
      grid-template-columns: 1fr !important;
    }
  }
`;

/* ─────────────────────────────────────────────────────────────────────────────
   Main Component
───────────────────────────────────────────────────────────────────────────── */

const AnalyticsDashboardScreen = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  // Queries
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useCatalogStats();
  const { data: categories, isLoading: categoriesLoading, refetch: refetchCategories } = useCategoryPriceSummary();
  const { data: topProducts, isLoading: productsLoading, refetch: refetchProducts } = useTopProducts(5);
  const { data: sentiment, isLoading: sentimentLoading, refetch: refetchSentiment } = useReviewSentiment();
  const { data: ragStatus } = useRAGStatus();

  const handleRefresh = () => {
    refetchStats();
    refetchCategories();
    refetchProducts();
    refetchSentiment();
    setRefreshKey((k) => k + 1);
  };

  const isLoading = statsLoading || categoriesLoading || productsLoading || sentimentLoading;

  // Sentiment calculations
  const sentimentTotal = sentiment?.total_reviews || 1;
  const posPercent = ((sentiment?.positive || 0) / sentimentTotal) * 100;
  const neuPercent = ((sentiment?.neutral || 0) / sentimentTotal) * 100;
  const negPercent = ((sentiment?.negative || 0) / sentimentTotal) * 100;

  // Calculate total inventory value from categories
  const totalInventoryValue = categories?.reduce((sum, cat) => {
    return sum + (cat.avg_price || 0) * (cat.product_count || 0);
  }, 0) || 0;

  return (
    <>
      <style>{responsiveStyles}</style>
      <div style={styles.container}>
        <div style={styles.inner}>
          {/* Header */}
          <div style={styles.header}>
            <div>
              <h1 style={styles.title}>
                <FiActivity size={32} style={{ color: "#10b981" }} />
                Analytics Dashboard
              </h1>
              <p style={styles.subtitle}>
                Real-time insights powered by MCP Tools & RAG
              </p>
            </div>
            <button style={styles.refreshBtn} onClick={handleRefresh}>
              <FiRefreshCw size={16} className={isLoading ? "spin-animation" : ""} />
              Refresh
            </button>
          </div>

          {/* Main Stats */}
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statHeader}>
                <div style={styles.statIcon("linear-gradient(135deg, #3b82f6, #2563eb)")}>
                  <FiBox />
                </div>
                <div style={styles.statTrend(true)}>
                  <FiTrendingUp size={12} />
                  Active
                </div>
              </div>
              <div style={styles.statValue}>
                {statsLoading ? "..." : stats?.total_products || 0}
              </div>
              <div style={styles.statLabel}>Total Products</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statHeader}>
                <div style={styles.statIcon("linear-gradient(135deg, #10b981, #059669)")}>
                  <FiStar />
                </div>
                <div style={styles.statTrend(true)}>
                  <FiTrendingUp size={12} />
                  +{sentiment?.positive || 0}
                </div>
              </div>
              <div style={styles.statValue}>
                {sentimentLoading ? "..." : sentiment?.total_reviews || 0}
              </div>
              <div style={styles.statLabel}>Total Reviews</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statHeader}>
                <div style={styles.statIcon("linear-gradient(135deg, #f59e0b, #d97706)")}>
                  <FiLayers />
                </div>
              </div>
              <div style={styles.statValue}>
                {categoriesLoading ? "..." : categories?.length || 0}
              </div>
              <div style={styles.statLabel}>Categories</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statHeader}>
                <div style={styles.statIcon("linear-gradient(135deg, #8b5cf6, #7c3aed)")}>
                  <FiDollarSign />
                </div>
              </div>
              <div style={styles.statValue}>
                ${totalInventoryValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div style={styles.statLabel}>Est. Inventory Value</div>
            </div>
          </div>

          {/* Main Grid */}
          <div style={styles.grid} className="analytics-grid">
            {/* Categories Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cardTitle}>
                  <FiPieChart size={18} style={{ color: "#3b82f6" }} />
                  Category Breakdown
                </h3>
              </div>
              <div style={styles.cardBody}>
                {categoriesLoading ? (
                  <div style={styles.loadingState}>
                    <FiRefreshCw className="spin-animation" />
                    Loading categories...
                  </div>
                ) : (
                  categories?.map((cat, idx) => (
                    <div key={idx} style={styles.categoryRow}>
                      <span style={styles.categoryName}>{cat.category}</span>
                      <div style={styles.categoryStats}>
                        <span>{cat.product_count} items</span>
                        <span style={{ color: "#10b981" }}>
                          ${cat.avg_price?.toFixed(0)} avg
                        </span>
                        <span style={{ color: "#f59e0b" }}>
                          ${cat.min_price} - ${cat.max_price}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Sentiment Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cardTitle}>
                  <FiBarChart2 size={18} style={{ color: "#10b981" }} />
                  Review Sentiment
                </h3>
              </div>
              <div style={styles.cardBody}>
                {sentimentLoading ? (
                  <div style={styles.loadingState}>
                    <FiRefreshCw className="spin-animation" />
                    Analyzing sentiment...
                  </div>
                ) : (
                  <>
                    <div style={styles.sentimentBar}>
                      <div style={styles.sentimentSegment("#10b981", posPercent)}>
                        {posPercent > 15 && `${posPercent.toFixed(0)}%`}
                      </div>
                      <div style={styles.sentimentSegment("#f59e0b", neuPercent)}>
                        {neuPercent > 15 && `${neuPercent.toFixed(0)}%`}
                      </div>
                      <div style={styles.sentimentSegment("#ef4444", negPercent)}>
                        {negPercent > 15 && `${negPercent.toFixed(0)}%`}
                      </div>
                    </div>
                    <div style={styles.sentimentLegend}>
                      <div style={styles.legendItem}>
                        <div style={styles.legendDot("#10b981")} />
                        <span>Positive ({sentiment?.positive || 0})</span>
                      </div>
                      <div style={styles.legendItem}>
                        <div style={styles.legendDot("#f59e0b")} />
                        <span>Neutral ({sentiment?.neutral || 0})</span>
                      </div>
                      <div style={styles.legendItem}>
                        <div style={styles.legendDot("#ef4444")} />
                        <span>Negative ({sentiment?.negative || 0})</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Top Products */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cardTitle}>
                  <FiTrendingUp size={18} style={{ color: "#f59e0b" }} />
                  Top Rated Products
                </h3>
                <Link to="/" style={{ color: "#3b82f6", fontSize: "13px", textDecoration: "none" }}>
                  View All →
                </Link>
              </div>
              <div style={styles.cardBody}>
                {productsLoading ? (
                  <div style={styles.loadingState}>
                    <FiRefreshCw className="spin-animation" />
                    Loading products...
                  </div>
                ) : (
                  topProducts?.slice(0, 5).map((product, idx) => (
                    <div key={idx} style={styles.topProduct}>
                      <div style={styles.productRank}>{idx + 1}</div>
                      <img
                        src={product.image || "/images/placeholder.jpg"}
                        alt={product.name}
                        style={styles.productImage}
                        onError={(e) => {
                          e.target.src = "/images/placeholder.jpg";
                        }}
                      />
                      <div style={styles.productInfo}>
                        <Link
                          to={`/product/${product.id || product._id}`}
                          style={styles.productName}
                        >
                          {product.name}
                        </Link>
                        <div style={styles.productMeta}>
                          <span style={{ color: "#f59e0b" }}>
                            ⭐ {product.rating?.toFixed(1)}
                          </span>
                          <span style={{ color: "#10b981" }}>
                            ${product.price}
                          </span>
                          <span>{product.brand}</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* System Status */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cardTitle}>
                  <FiCpu size={18} style={{ color: "#8b5cf6" }} />
                  AI System Status
                </h3>
              </div>
              <div style={styles.cardBody}>
                <div style={styles.statusGrid}>
                  <div style={styles.statusCard("#10b981")}>
                    <div style={styles.statusValue}>
                      <FiDatabase size={20} />
                    </div>
                    <div style={styles.statusLabel}>MCP Server</div>
                    <div style={{ color: "#10b981", fontSize: "12px", marginTop: "4px" }}>
                      ● Online
                    </div>
                  </div>
                  <div style={styles.statusCard("#3b82f6")}>
                    <div style={styles.statusValue}>
                      <FiCpu size={20} />
                    </div>
                    <div style={styles.statusLabel}>LangGraph</div>
                    <div style={{ color: "#3b82f6", fontSize: "12px", marginTop: "4px" }}>
                      ● Ready
                    </div>
                  </div>
                  <div style={styles.statusCard(ragStatus?.status === "operational" ? "#f59e0b" : "#64748b")}>
                    <div style={styles.statusValue}>
                      <FiLayers size={20} />
                    </div>
                    <div style={styles.statusLabel}>RAG/Pinecone</div>
                    <div style={{ 
                      color: ragStatus?.status === "operational" ? "#f59e0b" : "#94a3b8", 
                      fontSize: "12px", 
                      marginTop: "4px" 
                    }}>
                      ● {ragStatus?.status === "operational" ? "Indexed" : "Ready"}
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: "20px", padding: "16px", background: "rgba(255,255,255,0.05)", borderRadius: "12px" }}>
                  <div style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "8px" }}>Available Tools</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {["search_products", "semantic_search", "recommend", "compare", "catalog_stats", "sentiment"].map((tool) => (
                      <span
                        key={tool}
                        style={{
                          padding: "4px 10px",
                          borderRadius: "6px",
                          background: "rgba(139,92,246,0.2)",
                          fontSize: "11px",
                          color: "#a78bfa",
                        }}
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin-animation {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </>
  );
};

export default AnalyticsDashboardScreen;
