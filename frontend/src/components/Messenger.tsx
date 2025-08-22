import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { User, Chat, Message } from '../types';
import apiService from '../services/api';

const Messenger: React.FC = () => {
  const { user, logout } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadUsers();
    loadChats();
  }, []);

  useEffect(() => {
    if (currentChat) {
      loadMessages(currentChat.id);
    }
  }, [currentChat]);

  const loadUsers = async () => {
    try {
      const usersData = await apiService.getUsers();
      setUsers(usersData);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadChats = async () => {
    try {
      const chatsData = await apiService.getChats();
      console.log('Chats loaded:', chatsData);
      setChats(chatsData);
    } catch (error) {
      console.error('Error loading chats:', error);
    }
  };

  const loadMessages = async (chatId: number) => {
    try {
      const messagesData = await apiService.getChatMessages(chatId);
      console.log('Messages loaded for chat', chatId, ':', messagesData);
      setMessages(messagesData.reverse());
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const createOrOpenChat = async (recipientId: number) => {
    console.log('Creating/opening chat with user:', recipientId);
    try {
      const chat = await apiService.createChat(recipientId);
      console.log('Chat created/opened:', chat);
      setCurrentChat(chat);
      await loadChats();
    } catch (error) {
      console.error('Error creating chat:', error);
      alert('Помилка створення чату: ' + error);
    }
  };

  const sendMessage = async () => {
    if (!currentChat || !newMessage.trim()) return;

    console.log('Sending message:', { chatId: currentChat.id, content: newMessage.trim() });
    setIsLoading(true);
    try {
      const message = await apiService.sendMessage(currentChat.id, newMessage.trim());
      console.log('Message sent successfully:', message);
      setMessages(prev => [...prev, message]);
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Помилка відправки повідомлення: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getChatName = (chat: Chat) => {
    const otherUserId = chat.creator_id === user?.id ? chat.recipient_id : chat.creator_id;
    const otherUser = users.find(u => u.id === otherUserId);
    return otherUser?.username || `User ${otherUserId}`;
  };

  const getMessageAuthor = (message: Message) => {
    if (message.author_id === user?.id) return 'Ви';
    const author = users.find(u => u.id === message.author_id);
    return author?.username || `User ${message.author_id}`;
  };

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-900">Meduzzen</h1>
            <button
              onClick={logout}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">Привіт, {user?.username}!</p>
        </div>

        {/* Users List */}
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Користувачі</h3>
          <div className="space-y-2">
            {users.map((userItem) => (
              <button
                key={userItem.id}
                onClick={() => createOrOpenChat(userItem.id)}
                className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-primary-700">
                      {userItem.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{userItem.username}</p>
                    <p className="text-xs text-gray-500">{userItem.email}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Chats List */}
        <div className="border-t border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Мої чати</h3>
          <div className="space-y-2">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setCurrentChat(chat)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  currentChat?.id === chat.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-gray-50'
                }`}
              >
                <p className="text-sm font-medium">{getChatName(chat)}</p>
                <p className="text-xs text-gray-500">Приватний чат</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentChat ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {getChatName(currentChat)}
              </h2>
              <p className="text-sm text-gray-500">Приватний чат</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.author_id === user?.id ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`message-bubble ${
                    message.author_id === user?.id ? 'message-sent' : 'message-received'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {getMessageAuthor(message)} • {new Date(message.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Message Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Введіть повідомлення..."
                  className="flex-1 input-field"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !newMessage.trim()}
                  className="btn-primary px-6"
                >
                  {isLoading ? '...' : 'Відправити'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="mx-auto h-16 w-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Виберіть чат</h3>
              <p className="text-gray-500">Виберіть користувача зі списку або створіть новий чат</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Messenger;
