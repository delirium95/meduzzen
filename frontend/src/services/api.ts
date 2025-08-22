import { 
  User, 
  Chat, 
  Message, 
  AuthResponse, 
  LoginForm, 
  RegisterForm,
  ApiError 
} from '../types';

const API_BASE = 'http://localhost:8000';

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'API request failed');
    }
    return response.json();
  }

  // Auth endpoints
  async register(data: RegisterForm): Promise<User> {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse<User>(response);
  }

  async login(data: LoginForm): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      body: formData
    });
    return this.handleResponse<AuthResponse>(response);
  }

  async logout(): Promise<void> {
    await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    localStorage.removeItem('token');
  }

  // User endpoints
  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE}/users`, {
      headers: this.getAuthHeaders()
    });
    return this.handleResponse<User[]>(response);
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE}/me`, {
      headers: this.getAuthHeaders()
    });
    return this.handleResponse<User>(response);
  }

  // Chat endpoints
  async createChat(recipientId: number): Promise<Chat> {
    const response = await fetch(`${API_BASE}/chats`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ recipient_id: recipientId })
    });
    return this.handleResponse<Chat>(response);
  }

  async getChats(): Promise<Chat[]> {
    const response = await fetch(`${API_BASE}/chats`, {
      headers: this.getAuthHeaders()
    });
    return this.handleResponse<Chat[]>(response);
  }

  async getChatParticipants(chatId: number): Promise<User[]> {
    const response = await fetch(`${API_BASE}/chats/${chatId}/participants`, {
      headers: this.getAuthHeaders()
    });
    return this.handleResponse<User[]>(response);
  }

  // Message endpoints
  async sendMessage(chatId: number, content: string): Promise<Message> {
    const response = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ content, chat_id: chatId })
    });
    return this.handleResponse<Message>(response);
  }

  async getChatMessages(chatId: number, skip = 0, limit = 50): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/chats/${chatId}/messages?skip=${skip}&limit=${limit}`, {
      headers: this.getAuthHeaders()
    });
    return this.handleResponse<Message[]>(response);
  }

  async editMessage(messageId: number, newContent: string): Promise<Message> {
    const formData = new FormData();
    formData.append('new_content', newContent);

    const response = await fetch(`${API_BASE}/messages/${messageId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: formData
    });
    return this.handleResponse<Message>(response);
  }

  async deleteMessage(messageId: number): Promise<void> {
    await fetch(`${API_BASE}/messages/${messageId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
  }

  // File endpoints
  async uploadFile(messageId: number, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/messages/${messageId}/files`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: formData
    });
    return this.handleResponse(response);
  }
}

export const apiService = new ApiService();
export default apiService;
