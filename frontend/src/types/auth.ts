export type UserRole = 'doctor' | 'hospital_staff';

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  hospital_name: string;
  created_at: string;
  updated_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: string;
  hospital_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
