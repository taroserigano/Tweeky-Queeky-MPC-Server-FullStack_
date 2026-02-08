import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import { BASE_URL, MCP_URL } from "../constants";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// ──────────────────────────────────────────────────────────────────────────────
// Catalog Queries (Read-only)
// ──────────────────────────────────────────────────────────────────────────────

export const useCatalogStats = () => {
  return useQuery({
    queryKey: ["mcp", "catalog", "stats"],
    queryFn: async () => {
      const { data } = await api.get(`${MCP_URL}/catalog/stats`);
      return data;
    },
  });
};

export const useCategoryPriceSummary = () => {
  return useQuery({
    queryKey: ["mcp", "catalog", "categories"],
    queryFn: async () => {
      const { data } = await api.get(`${MCP_URL}/catalog/categories`);
      return data;
    },
  });
};

export const useTopProducts = (limit = 5) => {
  return useQuery({
    queryKey: ["mcp", "catalog", "top", limit],
    queryFn: async () => {
      const { data } = await api.get(
        `${MCP_URL}/catalog/top-products?limit=${limit}`,
      );
      return data;
    },
  });
};

export const useTopReviewedProducts = (limit = 3, options = {}) => {
  return useQuery({
    queryKey: ["mcp", "catalog", "top-reviewed", limit],
    queryFn: async () => {
      const { data } = await api.get(
        `${MCP_URL}/catalog/top-reviewed?limit=${limit}`,
      );
      return data;
    },
    ...options,
  });
};

export const useProductSearch = (query, limit = 10, options = {}) => {
  return useQuery({
    queryKey: ["mcp", "catalog", "search", query, limit],
    queryFn: async () => {
      const { data } = await api.get(
        `${MCP_URL}/catalog/search?q=${encodeURIComponent(query)}&limit=${limit}`,
      );
      return data;
    },
    enabled: !!query && query.length > 0,
    ...options,
  });
};

export const useReviewSentiment = (productId = null) => {
  return useQuery({
    queryKey: ["mcp", "catalog", "sentiment", productId],
    queryFn: async () => {
      const url = productId
        ? `${MCP_URL}/catalog/sentiment?product_id=${productId}`
        : `${MCP_URL}/catalog/sentiment`;
      const { data } = await api.get(url);
      return data;
    },
  });
};

// ──────────────────────────────────────────────────────────────────────────────
// AI Mutations
// ──────────────────────────────────────────────────────────────────────────────

export const useAIRecommend = () => {
  return useMutation({
    mutationFn: async ({ preferences, budget, limit = 5 }) => {
      const { data } = await api.post(`${MCP_URL}/ai/recommend`, {
        preferences,
        budget,
        limit,
      });
      return data;
    },
  });
};

export const useAICompare = () => {
  return useMutation({
    mutationFn: async (productIds) => {
      const { data } = await api.post(`${MCP_URL}/ai/compare`, {
        product_ids: productIds,
      });
      return data;
    },
  });
};

export const useAICartSuggestion = () => {
  return useMutation({
    mutationFn: async ({ goal, budget }) => {
      const { data } = await api.post(`${MCP_URL}/ai/cart-suggestion`, {
        goal,
        budget,
      });
      return data;
    },
  });
};

export const useAIExplain = () => {
  return useMutation({
    mutationFn: async (productId) => {
      const { data } = await api.post(
        `${MCP_URL}/ai/explain?product_id=${productId}`,
      );
      return data;
    },
  });
};

export const useAIAsk = () => {
  return useMutation({
    mutationFn: async ({ productId, question }) => {
      const { data } = await api.post(`${MCP_URL}/ai/ask`, {
        product_id: productId,
        question,
      });
      return data;
    },
  });
};

export const useAIChat = () => {
  return useMutation({
    mutationFn: async ({ message, context }) => {
      const { data } = await api.post(`${MCP_URL}/ai/chat`, {
        message,
        context,
      });
      return data;
    },
  });
};

export const useMCPTools = () => {
  return useQuery({
    queryKey: ["mcp", "tools"],
    queryFn: async () => {
      const { data } = await api.get(`${MCP_URL}/tools`);
      return data;
    },
  });
};
