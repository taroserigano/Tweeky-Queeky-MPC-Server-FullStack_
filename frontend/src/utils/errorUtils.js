/**
 * Extract a human-readable error message string from various error formats.
 * Handles FastAPI validation errors ({detail: [{type, loc, msg, input, url}]}),
 * standard API errors ({detail: "string"} or {message: "string"}),
 * and Axios error objects.
 */
export const getErrorMessage = (error, fallback = "An error occurred") => {
  if (!error) return fallback;

  // String errors
  if (typeof error === "string") return error;

  // FastAPI / Axios response errors
  const data = error?.response?.data || error?.data;

  if (data) {
    // FastAPI detail field
    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;
      // Validation error array: [{type, loc, msg, input, url}, ...]
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((e) => {
            const field = e.loc
              ? e.loc.filter((l) => l !== "body").join(".")
              : "";
            const msg = e.msg || JSON.stringify(e);
            return field ? `${field}: ${msg}` : msg;
          })
          .join("; ");
      }
      // Object detail
      if (typeof data.detail === "object") {
        return (
          data.detail.msg || data.detail.message || JSON.stringify(data.detail)
        );
      }
    }
    // Express-style {message: "..."}
    if (typeof data.message === "string") return data.message;
    // {error: "..."}
    if (typeof data.error === "string") return data.error;
  }

  // Plain error.message
  if (typeof error.message === "string") return error.message;

  // error.error (react-query sometimes wraps it)
  if (typeof error.error === "string") return error.error;

  return fallback;
};
