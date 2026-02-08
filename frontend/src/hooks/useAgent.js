import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { BASE_URL } from "../constants";

// Use proxy for local dev, or BASE_URL for production
const AGENT_URL = `${BASE_URL}/api/agent`;

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

/**
 * Main chat hook - calls agent gateway which orchestrates MCP and RAG
 */
export const useAgentChat = () => {
  return useMutation({
    mutationFn: async ({ message, threadId, sessionId, userId }) => {
      const { data } = await api.post(`${AGENT_URL}/chat`, {
        message,
        thread_id: threadId || sessionId || undefined,
        user_id: userId,
      });
      return data;
    },
  });
};

/**
 * Health check for agent and backend services
 */
export const useAgentHealth = () => {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.get("/api/health");
      return data;
    },
  });
};
