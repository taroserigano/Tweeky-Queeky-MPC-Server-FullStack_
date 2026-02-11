import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { BASE_URL, ORDERS_URL, PAYPAL_URL, STRIPE_URL } from "../constants";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 30000, // 30 second timeout to prevent hanging
});

export const useCreateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (order) => {
      console.log("[API] Creating order:", order);
      try {
        const { data } = await api.post(ORDERS_URL, order);
        console.log("[API] Order created successfully:", data._id);
        return data;
      } catch (error) {
        console.error("[API] Order creation failed:", error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["orders"]);
    },
  });
};

export const useOrderDetails = (orderId) => {
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: async () => {
      const { data } = await api.get(`${ORDERS_URL}/${orderId}`);
      return data;
    },
    enabled: !!orderId,
  });
};

export const useUpdateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ orderId, updateData }) => {
      const { data } = await api.put(
        `${ORDERS_URL}/${orderId}/update-details`,
        updateData,
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(["order", variables.orderId]);
    },
  });
};

export const usePayOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ orderId, details }) => {
      const { data } = await api.put(`${ORDERS_URL}/${orderId}/pay`, details);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(["order", variables.orderId]);
      queryClient.invalidateQueries(["orders"]);
    },
  });
};

export const usePayPalClientId = () => {
  return useQuery({
    queryKey: ["paypal", "clientId"],
    queryFn: async () => {
      const { data } = await api.get(PAYPAL_URL);
      return data;
    },
    staleTime: Infinity,
  });
};

export const useStripePublishableKey = () => {
  return useQuery({
    queryKey: ["stripe", "publishableKey"],
    queryFn: async () => {
      const { data } = await api.get(STRIPE_URL);
      return data;
    },
    staleTime: Infinity,
  });
};

export const useCreatePaymentIntent = () => {
  return useMutation({
    mutationFn: async (orderId) => {
      const { data } = await api.post(
        `${ORDERS_URL}/${orderId}/stripe-payment-intent`,
      );
      return data;
    },
  });
};

export const useMyOrders = () => {
  return useQuery({
    queryKey: ["orders", "mine"],
    queryFn: async () => {
      const { data } = await api.get(`${ORDERS_URL}/mine`);
      return data;
    },
  });
};

export const useOrders = () => {
  return useQuery({
    queryKey: ["orders", "all"],
    queryFn: async () => {
      const { data } = await api.get(ORDERS_URL);
      return data;
    },
  });
};

export const useDeliverOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderId) => {
      const { data } = await api.put(`${ORDERS_URL}/${orderId}/deliver`, {});
      return data;
    },
    onSuccess: (_, orderId) => {
      queryClient.invalidateQueries(["order", orderId]);
      queryClient.invalidateQueries(["orders"]);
    },
  });
};
