import { useState, useRef, useEffect } from "react";
import { FiSend, FiMessageSquare } from "react-icons/fi";
import { useAgentChat } from "../hooks/useAgent";

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "650px",
    background: "#fff",
    borderRadius: "16px",
    border: "1px solid #e2e8f0",
    overflow: "hidden",
  },
  header: {
    padding: "16px 20px",
    background: "linear-gradient(135deg, #10b981, #059669)",
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
  headerTitle: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
  },
  statusBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    borderRadius: "12px",
    background: "rgba(255,255,255,0.2)",
    fontSize: "11px",
  },
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
    padding: "40px 20px",
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
  message: (isUser) => ({
    display: "flex",
    flexDirection: "column",
    alignItems: isUser ? "flex-end" : "flex-start",
    gap: "6px",
  }),
  messageBubble: (isUser) => ({
    maxWidth: "80%",
    padding: "12px 16px",
    borderRadius: "16px",
    background: isUser ? "linear-gradient(135deg, #10b981, #059669)" : "#fff",
    color: isUser ? "#fff" : "#1e293b",
    border: isUser ? "none" : "1px solid #e2e8f0",
    fontSize: "14px",
    lineHeight: "1.5",
    whiteSpace: "pre-wrap",
  }),
  messageLabel: {
    fontSize: "11px",
    color: "#94a3b8",
    fontWeight: "500",
  },
  toolsBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "2px 8px",
    borderRadius: "8px",
    background: "#e0f2fe",
    color: "#0369a1",
    fontSize: "10px",
    fontWeight: "500",
    marginTop: "4px",
  },
  inputArea: {
    padding: "16px 20px",
    borderTop: "1px solid #e2e8f0",
    background: "#fff",
  },
  inputContainer: {
    display: "flex",
    gap: "12px",
  },
  input: {
    flex: 1,
    padding: "12px 16px",
    border: "1px solid #e2e8f0",
    borderRadius: "12px",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.2s",
  },
  sendButton: (disabled) => ({
    padding: "12px 20px",
    background: disabled
      ? "#e2e8f0"
      : "linear-gradient(135deg, #10b981, #059669)",
    color: disabled ? "#94a3b8" : "#fff",
    border: "none",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: "500",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "opacity 0.2s",
  }),
};

const SimpleAgentChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const chatMutation = useAgentChat();

  // Auto-scroll only when receiving assistant messages
  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === "assistant") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await chatMutation.mutateAsync({
        message: userMessage,
      });

      const messageContent =
        response?.message || response?.reply || "No message in response";

      // Add agent response
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: messageContent,
          used: response?.used,
          debug: response?.debug,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Sorry, I encountered an error. Please try again.",
          error: true,
        },
      ]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <FiMessageSquare size={20} />
          <h3 style={styles.headerTitle}>Smart Shopping Agent</h3>
        </div>
        <div style={styles.statusBadge}>
          <div
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: "#4ade80",
            }}
          />
          Online
        </div>
      </div>

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 ? (
          <div style={styles.welcomeBox}>
            <div style={styles.welcomeIcon}>
              <FiMessageSquare />
            </div>
            <h4 style={styles.welcomeTitle}>How can I help you today?</h4>
            <p style={{ fontSize: "14px", marginBottom: "16px" }}>
              Try asking about:
            </p>
            <div style={{ fontSize: "13px", color: "#64748b" }}>
              • "Show me headphones under $300"
              <br />
              • "Track order ORD-1001"
              <br />
              • "What's your return policy?"
              <br />• "Recommend a laptop for work"
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} style={styles.message(msg.role === "user")}>
                <span style={styles.messageLabel}>
                  {msg.role === "user" ? "You" : "Agent"}
                </span>
                <div style={styles.messageBubble(msg.role === "user")}>
                  {msg.content}
                </div>
                {msg.used && (
                  <div style={styles.toolsBadge}>
                    {msg.used.mcpTools?.length > 0 &&
                      `🔧 ${msg.used.mcpTools.join(", ")}`}
                    {msg.used.rag && " 📚 RAG"}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={styles.inputArea}>
        <div style={styles.inputContainer}>
          <input
            style={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={chatMutation.isPending}
          />
          <button
            style={styles.sendButton(chatMutation.isPending || !input.trim())}
            onClick={handleSend}
            disabled={chatMutation.isPending || !input.trim()}
          >
            <FiSend size={16} />
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimpleAgentChat;
