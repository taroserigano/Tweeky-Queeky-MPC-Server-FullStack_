import { useState } from "react";
import { Link } from "react-router-dom";
import {
  FiMessageSquare,
  FiBarChart2,
  FiZap,
  FiSearch,
  FiTool,
  FiLayers,
  FiDatabase,
  FiCpu,
} from "react-icons/fi";
import SmartAgentChat from "../components/SmartAgentChat";
import { useAgentStatus } from "../hooks/useAgentQueries";

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
    marginBottom: "24px",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    background: "linear-gradient(135deg, #10b981, #059669)",
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
    margin: "0 auto 24px",
  },
  tabs: {
    display: "flex",
    justifyContent: "center",
    gap: "8px",
    marginBottom: "24px",
    flexWrap: "wrap",
  },
  tab: (active) => ({
    padding: "12px 24px",
    background: active ? "linear-gradient(135deg, #10b981, #059669)" : "#fff",
    color: active ? "#fff" : "#64748b",
    border: active ? "none" : "1px solid #e2e8f0",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: "500",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    transition: "all 0.2s",
  }),
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 350px",
    gap: "24px",
  },
  mainArea: {
    minHeight: "600px",
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
  featureItem: {
    display: "flex",
    gap: "12px",
    padding: "12px 0",
    borderBottom: "1px solid #f1f5f9",
  },
  featureIcon: (color) => ({
    width: "36px",
    height: "36px",
    borderRadius: "10px",
    background: color,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: "16px",
    flexShrink: 0,
  }),
  featureInfo: {
    flex: 1,
  },
  featureName: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: "2px",
  },
  featureDesc: {
    fontSize: "12px",
    color: "#64748b",
    lineHeight: "1.4",
  },
  statRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "10px 0",
    borderBottom: "1px solid #f1f5f9",
  },
  statLabel: {
    fontSize: "13px",
    color: "#64748b",
  },
  statValue: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#1e293b",
  },
  linkBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    padding: "12px",
    background: "linear-gradient(135deg, #3b82f6, #2563eb)",
    color: "#fff",
    borderRadius: "10px",
    textDecoration: "none",
    fontSize: "13px",
    fontWeight: "500",
    marginTop: "12px",
  },
};

const responsiveStyles = `
  @media (max-width: 1024px) {
    .ai-grid {
      grid-template-columns: 1fr !important;
    }
    .ai-sidebar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }
  }
`;

/* ─────────────────────────────────────────────────────────────────────────────
   Main Component
───────────────────────────────────────────────────────────────────────────── */

const AIHubScreen = () => {
  const [activeTab, setActiveTab] = useState("agent");
  const { data: agentStatus } = useAgentStatus();

  const tabs = [
    { id: "agent", label: "Smart Agent", icon: <FiMessageSquare /> },
    { id: "mcp", label: "MCP Tools", icon: <FiDatabase /> },
  ];

  const catalogStats = {
    total_products: 40,
    total_reviews: 819,
    categories: ["Electronics", "Fashion", "Home"],
  };

  const features = [
    {
      icon: <FiSearch />,
      color: "linear-gradient(135deg, #3b82f6, #2563eb)",
      name: "Semantic Search",
      desc: "Natural language product discovery using RAG",
    },
    {
      icon: <FiMessageSquare />,
      color: "linear-gradient(135deg, #10b981, #059669)",
      name: "Conversational AI",
      desc: "Multi-turn conversations with context memory",
    },
    {
      icon: <FiTool />,
      color: "linear-gradient(135deg, #f59e0b, #d97706)",
      name: "Tool Calling",
      desc: "Intelligent tool selection via LangGraph agent",
    },
    {
      icon: <FiLayers />,
      color: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
      name: "Vector Search",
      desc: "Pinecone-powered similarity matching",
    },
  ];

  return (
    <>
      <style>{responsiveStyles}</style>
      <div style={styles.container}>
        <div style={styles.inner}>
          {/* Header */}
          <header style={styles.header}>
            <span style={styles.badge}>
              <FiZap size={14} />
              AI-Powered Shopping
            </span>
            <h1 style={styles.title}>AI Assistant Hub</h1>
            <p style={styles.subtitle}>
              Chat with our smart shopping assistant powered by LangGraph, RAG,
              and MCP. Get product recommendations, compare items, and build
              carts within your budget.
            </p>
          </header>

          {/* Tabs */}
          <div style={styles.tabs}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                style={styles.tab(activeTab === tab.id)}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Main Grid */}
          <div style={styles.grid} className="ai-grid">
            {/* Main Chat Area */}
            <div style={styles.mainArea}>
              {activeTab === "agent" ? (
                <SmartAgentChat height="650px" />
              ) : (
                <div
                  style={{
                    ...styles.card,
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <div
                    style={{
                      ...styles.cardHeader,
                      background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                      color: "#fff",
                    }}
                  >
                    <FiDatabase size={20} />
                    <h3 style={{ ...styles.cardTitle, color: "#fff" }}>
                      MCP Catalog Tools
                    </h3>
                  </div>
                  <div
                    style={{
                      flex: 1,
                      padding: "24px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        width: "80px",
                        height: "80px",
                        borderRadius: "20px",
                        background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        marginBottom: "20px",
                      }}
                    >
                      <FiDatabase size={36} style={{ color: "#fff" }} />
                    </div>
                    <h3
                      style={{
                        fontSize: "20px",
                        fontWeight: "600",
                        marginBottom: "12px",
                        color: "#1e293b",
                      }}
                    >
                      MCP Catalog Tools
                    </h3>
                    <p
                      style={{
                        fontSize: "14px",
                        color: "#64748b",
                        maxWidth: "400px",
                        lineHeight: "1.6",
                        marginBottom: "24px",
                      }}
                    >
                      Access 24+ MCP tools for catalog browsing, analytics, and
                      admin operations. View category breakdowns, sentiment
                      analysis, and product insights.
                    </p>
                    <Link to="/ai-assistant" style={styles.linkBtn}>
                      <FiBarChart2 size={16} />
                      Open Full Catalog View
                    </Link>
                    <Link
                      to="/analytics"
                      style={{
                        ...styles.linkBtn,
                        marginTop: "8px",
                        background: "linear-gradient(135deg, #0f172a, #1e293b)",
                      }}
                    >
                      <FiBarChart2 size={16} />
                      View Analytics Dashboard
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div style={styles.sidebar} className="ai-sidebar">
              {/* AI Capabilities */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div
                    style={styles.cardIcon(
                      "linear-gradient(135deg, #10b981, #059669)",
                    )}
                  >
                    <FiCpu size={14} />
                  </div>
                  <h3 style={styles.cardTitle}>AI Capabilities</h3>
                </div>
                <div style={styles.cardBody}>
                  {features.map((feature, idx) => (
                    <div key={idx} style={styles.featureItem}>
                      <div style={styles.featureIcon(feature.color)}>
                        {feature.icon}
                      </div>
                      <div style={styles.featureInfo}>
                        <div style={styles.featureName}>{feature.name}</div>
                        <div style={styles.featureDesc}>{feature.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Stats */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div
                    style={styles.cardIcon(
                      "linear-gradient(135deg, #3b82f6, #2563eb)",
                    )}
                  >
                    <FiBarChart2 size={14} />
                  </div>
                  <h3 style={styles.cardTitle}>Catalog Stats</h3>
                </div>
                <div style={styles.cardBody}>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Total Products</span>
                    <span style={styles.statValue}>
                      {catalogStats?.total_products || "—"}
                    </span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Total Reviews</span>
                    <span style={styles.statValue}>
                      {catalogStats?.total_reviews || "—"}
                    </span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Categories</span>
                    <span style={styles.statValue}>
                      {catalogStats?.categories?.length || "—"}
                    </span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Agent Status</span>
                    <span
                      style={{
                        ...styles.statValue,
                        color:
                          agentStatus?.status === "operational"
                            ? "#10b981"
                            : "#64748b",
                      }}
                    >
                      {agentStatus?.status === "operational"
                        ? "● Online"
                        : "● Offline"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Tech Stack */}
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <div
                    style={styles.cardIcon(
                      "linear-gradient(135deg, #f59e0b, #d97706)",
                    )}
                  >
                    <FiZap size={14} />
                  </div>
                  <h3 style={styles.cardTitle}>Tech Stack</h3>
                </div>
                <div style={styles.cardBody}>
                  <div
                    style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}
                  >
                    {[
                      "LangGraph",
                      "LangChain",
                      "OpenAI",
                      "Pinecone",
                      "FastMCP",
                      "MongoDB",
                    ].map((tech) => (
                      <span
                        key={tech}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "8px",
                          background: "#f1f5f9",
                          fontSize: "12px",
                          color: "#475569",
                          fontWeight: "500",
                        }}
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AIHubScreen;
