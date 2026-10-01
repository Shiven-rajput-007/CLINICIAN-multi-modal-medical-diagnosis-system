const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface RequestOptions extends RequestInit {
  data?: unknown;
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { data, headers: customHeaders, ...customConfig } = options;

  const token = localStorage.getItem('medical_auth_token');

  const headers: Record<string, string> = {
    ...((customHeaders as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let body: BodyInit | null | undefined = undefined;

  if (data instanceof FormData) {
    body = data;
    // Browser sets multipart/form-data with boundary automatically
  } else if (data !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(data);
  }

  const config: RequestInit = {
    ...customConfig,
    headers,
    body,
  };

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, config);

  if (response.status === 401) {
    // If unauthorized, clear token and notify application
    localStorage.removeItem('medical_auth_token');
    localStorage.removeItem('medical_auth_user');
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  if (response.status === 204) {
    return {} as T;
  }

  let responseData: unknown;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    responseData = await response.json();
  } else {
    responseData = await response.text();
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    if (responseData && typeof responseData === 'object' && 'detail' in responseData) {
      const detail = (responseData as { detail: unknown }).detail;
      errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
    }
    throw new ApiError(errorMessage, response.status, responseData);
  }

  return responseData as T;
}
