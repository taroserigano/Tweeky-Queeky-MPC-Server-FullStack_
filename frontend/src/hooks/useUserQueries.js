import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { BASE_URL, USERS_URL } from '../constants';

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Required for JWT authentication
});

export const useLogin = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ email, password }) => {
      const { data } = await api.post(`${USERS_URL}/auth`, { email, password });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['user', 'profile']);
    },
  });
};

export const useRegister = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ name, email, password }) => {
      const { data } = await api.post(USERS_URL, { name, email, password });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['user', 'profile']);
    },
  });
};

// Clear all React Query caches on logout to prevent data leakage
export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`${USERS_URL}/logout`);
      return data;
    },
    onSuccess: () => {
      queryClient.clear();
    },
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (userData) => {
      const { data } = await api.put(`${USERS_URL}/profile`, userData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['user', 'profile']);
    },
  });
};

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await api.get(USERS_URL);
      return data;
    },
  });
};

export const useUserDetails = (userId) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const { data } = await api.get(`${USERS_URL}/${userId}`);
      return data;
    },
    enabled: !!userId,
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (userId) => {
      const { data } = await api.delete(`${USERS_URL}/${userId}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ userId, ...userData }) => {
      const { data } = await api.put(`${USERS_URL}/${userId}`, userData);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['user', variables.userId]);
      queryClient.invalidateQueries(['users']);
    },
  });
};
