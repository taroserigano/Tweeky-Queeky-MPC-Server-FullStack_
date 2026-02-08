import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { BASE_URL } from "../constants";

const AGENT_URL = "/api/agent";
const RAG_URL = "/api/rag";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// ──────────────────────────────────────────────────────────────────────────────
// LangGraph Agent Chat
// ──────────────────────────────────────────────────────────────────────────────

/**
 * Main chat hook for LangGraph agent
 * Supports conversation threading and tool calling
 */
export const useAgentChat = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ message, threadId, userId }) => {
      const response = await api.post(`${AGENT_URL}/chat`, {
        message,
        thread_id: threadId,
        user_id: userId,
      });
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate thread history on successful message
      queryClient.invalidateQueries(["agent", "thread", data.thread_id]);
    },
  });
};

/**
 * Streaming chat - returns an async generator
 */
export const useAgentChatStream = () => {
  return useMutation({
    mutationFn: async ({ message, threadId }) => {
      const response = await fetch(`${BASE_URL}${AGENT_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message, thread_id: threadId }),
      });

      if (!response.ok) {
        throw new Error("Stream failed");
      }

      return response;
    },
  });
};

/**
 * Get conversation history for a thread
 */
export const useThreadHistory = (threadId, options = {}) => {
  return useQuery({
    queryKey: ["agent", "thread", threadId],
    queryFn: async () => {
      const { data } = await api.get(`${AGENT_URL}/thread/${threadId}`);
      return data;
    },
    enabled: !!threadId,
    ...options,
  });
};

/**
 * List all threads for a user
 */
export const useUserThreads = (userId, options = {}) => {
  return useQuery({
    queryKey: ["agent", "threads", userId],
    queryFn: async () => {
      const { data } = await api.get(`${AGENT_URL}/threads?user_id=${userId}`);
      return data;
    },
    enabled: !!userId,
    ...options,
  });
};

/**
 * Get agent status and capabilities
 */
export const useAgentStatus = (options = {}) => {
  return useQuery({
    queryKey: ["agent", "status"],
    queryFn: async () => {
      const { data } = await api.get(`${AGENT_URL}/status`);
      return data;
    },
    staleTime: 60000, // 1 minute
    ...options,
  });
};

// ──────────────────────────────────────────────────────────────────────────────
// RAG Service Queries
// ──────────────────────────────────────────────────────────────────────────────

/**
 * Semantic search using RAG
 */
export const useRAGSearch = () => {
  return useMutation({
    mutationFn: async ({ query, maxPrice, minRating, category, topK = 5 }) => {
      const params = new URLSearchParams();
      params.append("query", query);
      if (maxPrice) params.append("max_price", maxPrice);
      if (minRating) params.append("min_rating", minRating);
      if (category) params.append("category", category);
      params.append("top_k", topK);

      const { data } = await api.get(`${RAG_URL}/search?${params}`);
      return data;
    },
  });
};

/**
 * RAG-powered recommendations
 */
export const useRAGRecommend = () => {
  return useMutation({
    mutationFn: async ({ preferences, budget, limit = 5 }) => {
      const { data } = await api.post(`${RAG_URL}/recommend`, {
        preferences,
        budget,
        limit,
      });
      return data;
    },
  });
};

/**
 * RAG-powered product comparison
 */
export const useRAGCompare = () => {
  return useMutation({
    mutationFn: async (productIds) => {
      const { data } = await api.post(`${RAG_URL}/compare`, {
        product_ids: productIds,
      });
      return data;
    },
  });
};

/**
 * RAG service status
 */
export const useRAGStatus = (options = {}) => {
  return useQuery({
    queryKey: ["rag", "status"],
    queryFn: async () => {
      const { data } = await api.get(`${RAG_URL}/status`);
      return data;
    },
    staleTime: 60000,
    ...options,
  });
};

/**
 * Reindex products in vector store
 */
export const useRAGReindex = () => {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`${RAG_URL}/reindex`);
      return data;
    },
  });
};

// ──────────────────────────────────────────────────────────────────────────────
// Quick Actions - Predefined agent queries
// ──────────────────────────────────────────────────────────────────────────────

export const QUICK_ACTIONS = [
  {
    id: "find-headphones",
    label: "🎧 Find headphones",
    query: "Find me the best wireless headphones for music",
    icon: "headphones",
  },
  {
    id: "budget-laptop",
    label: "💻 Budget laptop",
    query: "I need a good laptop under $800 for work",
    icon: "laptop",
  },
  {
    id: "gift-ideas",
    label: "🎁 Gift ideas",
    query: "Suggest gift ideas for a tech enthusiast around $100",
    icon: "gift",
  },
  {
    id: "home-office",
    label: "🏠 Home office setup",
    query: "Help me build a home office setup for $500",
    icon: "home",
  },
  {
    id: "compare-products",
    label: "⚖️ Compare items",
    query: "Compare the top-rated products in Electronics",
    icon: "compare",
  },
  {
    id: "trending",
    label: "🔥 What's trending",
    query: "What are the most popular products right now?",
    icon: "trending",
  },
];
