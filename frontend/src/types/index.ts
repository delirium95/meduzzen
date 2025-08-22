export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Chat {
  id: number;
  name?: string;
  description?: string;
  chat_type: 'private';
  creator_id: number;
  recipient_id: number;
  created_at: string;
  is_active: boolean;
}

export interface Message {
  id: number;
  content: string;
  message_type: 'text' | 'file' | 'system';
  author_id: number;
  chat_id: number;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface FileAttachment {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  message_id: number;
  uploaded_at: string;
}

export interface ChatMember {
  id: number;
  user_id: number;
  chat_id: number;
  role: 'participant';
  status: 'active' | 'blocked' | 'left';
  joined_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
}

export interface ApiError {
  detail: string;
}
