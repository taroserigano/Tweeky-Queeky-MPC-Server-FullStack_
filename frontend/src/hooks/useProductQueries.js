import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { BASE_URL, PRODUCTS_URL } from "../constants";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

export const useProducts = (keyword = "", pageNumber = 1, sortBy = "") => {
  return useQuery({
    queryKey: ["products", keyword, pageNumber, sortBy],
    queryFn: async () => {
      const params = {};
      if (keyword) params.keyword = keyword;
      if (pageNumber) params.pageNumber = pageNumber;
      if (sortBy) params.sortBy = sortBy;

      const { data } = await api.get(PRODUCTS_URL, { params });
      return data;
    },
  });
};

export const useProductDetails = (productId) => {
  return useQuery({
    queryKey: ["product", productId],
    queryFn: async () => {
      const { data } = await api.get(`${PRODUCTS_URL}/${productId}`);
      return data;
    },
    enabled: !!productId,
  });
};

export const useTopProducts = () => {
  return useQuery({
    queryKey: ["products", "top"],
    queryFn: async () => {
      const { data } = await api.get(`${PRODUCTS_URL}/top`);
      return data;
    },
  });
};

export const useCreateReview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ productId, rating, comment }) => {
      const { data } = await api.post(`${PRODUCTS_URL}/${productId}/reviews`, {
        rating,
        comment,
      });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(["product", variables.productId]);
      queryClient.invalidateQueries(["products"]);
    },
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (product) => {
      const { data } = await api.post(PRODUCTS_URL, product);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["products"]);
    },
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ productId, ...product }) => {
      const { data } = await api.put(`${PRODUCTS_URL}/${productId}`, product);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(["product", variables.productId]);
      queryClient.invalidateQueries(["products"]);
    },
  });
};

export const useDeleteProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (productId) => {
      const { data } = await api.delete(`${PRODUCTS_URL}/${productId}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(["products"]);
    },
  });
};

export const useUploadProductImage = () => {
  return useMutation({
    mutationFn: async (formData) => {
      const { data } = await api.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return data;
    },
  });
};
