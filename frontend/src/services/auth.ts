import { apiClient } from './api';
import { User, LoginCredentials, RegisterData, AuthResponse } from '../types';

export const authService = {
  async register(data: RegisterData): Promise<User> {
    return apiClient<User>('/auth/register', {
      method: 'POST',
      data,
    });
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return apiClient<AuthResponse>('/auth/login', {
      method: 'POST',
      data: credentials,
    });
  },

  async getMe(): Promise<User> {
    return apiClient<User>('/auth/me', {
      method: 'GET',
    });
  },
};
