// React Query Hooks - Central export module

export {
  useCreateOrder,
  useOrderDetails,
  usePayOrder,
  usePayPalClientId,
  useMyOrders,
  useOrders,
  useDeliverOrder,
} from './useOrderQueries';

export {
  useProducts,
  useProductDetails,
  useTopProducts,
  useCreateReview,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  useUploadProductImage,
} from './useProductQueries';

export {
  useLogin,
  useRegister,
  useLogout,
  useUpdateProfile,
  useUsers,
  useUserDetails,
  useDeleteUser,
  useUpdateUser,
} from './useUserQueries';

