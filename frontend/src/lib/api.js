import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
export const API_URL = `${API_BASE_URL}/api`;
export const DEFAULT_USER_ID = process.env.REACT_APP_DEFAULT_USER_ID || "default_user";

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 20000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      "Request failed";
    return Promise.reject(new Error(message));
  }
);

export const api = {
  get: (url, config = {}) => apiClient.get(url, config).then((res) => res.data),
  post: (url, data = {}, config = {}) => apiClient.post(url, data, config).then((res) => res.data),
  patch: (url, data = {}, config = {}) => apiClient.patch(url, data, config).then((res) => res.data),
  delete: (url, config = {}) => apiClient.delete(url, config).then((res) => res.data),
};

export const handleApiError = (error, fallbackMessage = "Something went wrong") => {
  if (error instanceof Error) {
    return error.message || fallbackMessage;
  }
  return fallbackMessage;
};
