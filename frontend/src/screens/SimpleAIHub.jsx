import SimpleAgentChat from "../components/SimpleAgentChat";
import { FiZap, FiMessageSquare, FiSearch, FiTool, FiLayers } from "react-icons/fi";

const styles = {
  container: {
    minHeight: "calc(100vh - 120px)",
    background: "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
    padding: "24px 16px",
  },
  inner: {
    maxWidth: "1200px",
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
    background: "linear-gradient(135deg, #10b981, #059669)",
    color: "#fff",
    padding: "6px 14px",
    borderRadius: "50px",
    fontSize: "12px",
    fontWeight: "600",
    marginBottom: "12px",
  },
  title: {
    fontSize: "36px",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "12px",
  },
  subtitle: {
    fontSize: "16px",
    color: "#64748b",
    maxWidth: "700px",
    margin: "0 auto 24px",
    lineHeight: "1.6",
  },
  architecture: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "16px",
    marginBottom: "32px",
  },
  archCard: {
    background: "#fff",
    padding: "20px",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
    textAlign: "center",
  },
  archIcon: (color) => ({
    width: "48px",
    height: "48px",
    borderRadius: "12px",
    background: color,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 12px",
    color: "#fff",
    fontSize: "20px",
  }),
  archTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: "6px",
  },
  archDesc: {
    fontSize: "12px",
    color: "#64748b",
    lineHeight: "1.4",
  },
  chatContainer: {
    maxWidth: "900px",
    margin: "0 auto",
  },
};

const SimpleAIHub = () => {
  return (
    <div style={styles.container}>
      <div style={styles.inner}>
        {/* Header */}
        <div style={styles.header}>
          <span style={styles.badge}>
            <FiZap size={14} />
            3-Service Architecture
          </span>
          <h1 style={styles.title}>AI Shopping Assistant</h1>
          <p style={styles.subtitle}>
            Clean MCP/RAG/Agent architecture. The agent orchestrates MCP tools (product/order data) 
            and RAG (document search) behind the scenes. Frontend only talks to the agent.
          </p>
        </div>

        {/* Architecture Overview */}
        <div style={styles.architecture}>
          <div style={styles.archCard}>
            <div style={styles.archIcon("linear-gradient(135deg, #3b82f6, #2563eb)")}>
              <FiMessageSquare />
            </div>
            <div style={styles.archTitle}>Agent Gateway</div>
            <div style={styles.archDesc}>
              Port 7000 - Routes queries to MCP or RAG
            </div>
          </div>

          <div style={styles.archCard}>
            <div style={styles.archIcon("linear-gradient(135deg, #f59e0b, #d97706)")}>
              <FiTool />
            </div>
            <div style={styles.archTitle}>MCP Server</div>
            <div style={styles.archDesc}>
              Port 7001 - Product & order tools
            </div>
          </div>

          <div style={styles.archCard}>
            <div style={styles.archIcon("linear-gradient(135deg, #8b5cf6, #7c3aed)")}>
              <FiSearch />
            </div>
            <div style={styles.archTitle}>RAG Service</div>
            <div style={styles.archDesc}>
              Port 7002 - TF-IDF document retrieval
            </div>
          </div>

          <div style={styles.archCard}>
            <div style={styles.archIcon("linear-gradient(135deg, #10b981, #059669)")}>
              <FiLayers />
            </div>
            <div style={styles.archTitle}>Frontend</div>
            <div style={styles.archDesc}>
              Only calls agent - MCP hidden
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div style={styles.chatContainer}>
          <SimpleAgentChat />
        </div>
      </div>
    </div>
  );
};

export default SimpleAIHub;
