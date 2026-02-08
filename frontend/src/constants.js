// Automatically detect environment
// When running in Docker, REACT_APP_API_URL will be set
// When running locally, it uses the proxy from package.json
export const BASE_URL = process.env.REACT_APP_API_URL || "";
export const PRODUCTS_URL = "/api/products";
export const USERS_URL = "/api/users";
export const ORDERS_URL = "/api/orders";
export const PAYPAL_URL = "/api/config/paypal";
export const STRIPE_URL = "/api/config/stripe";
export const MCP_URL = "/api/mcp";
