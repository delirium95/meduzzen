# 💬 Meduzzen Messenger

Сучасний веб-додаток месенджер з приватними чатами один-на-один, реалізований на **FastAPI + React + TypeScript** з **Tailwind CSS**.

## 🏗️ Архітектура

- **Backend**: Python FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Авторизація**: JWT токени + OAuth2
- **База даних**: PostgreSQL

## ✨ Особливості

- 🔐 **JWT авторизація** - безпечна автентифікація користувачів
- 👥 **Приватні чати** - спілкування один-на-один
- 💬 **Повідомлення** - відправлення, редагування, видалення
- 📎 **Файли** - прикріплення файлів до повідомлень
- 🌐 **Сучасний UI** - React + TypeScript + Tailwind CSS
- 🗄️ **PostgreSQL** - надійне зберігання даних
- 📱 **Responsive дизайн** - для всіх пристроїв

## 🚀 Швидкий старт

### 1. Backend (FastAPI)

```bash
# Активація віртуального середовища
venv\Scripts\activate

# Встановлення залежностей
pip install -r requirements.txt

# Налаштування бази даних в config.env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meduzzen_db

# Запуск сервера
uvicorn main:app --reload
```

Backend буде доступний за адресою: **http://localhost:8000**

### 2. Frontend (React)

```bash
# Перехід в папку фронтенду
cd frontend

# Встановлення залежностей
npm install

# Запуск в режимі розробки
npm start
```

Frontend буде доступний за адресою: **http://localhost:3000**

## 📁 Структура проекту

```
meduzzen/
├── backend/                    # FastAPI бекенд
│   ├── main.py               # FastAPI додаток та API endpoints
│   ├── models.py             # Pydantic та SQLAlchemy моделі
│   ├── database.py           # Налаштування бази даних
│   ├── auth.py               # JWT авторизація
│   ├── chat_operations.py    # Бізнес-логіка чатів
│   ├── requirements.txt      # Python залежності
│   └── config.env            # Конфігурація
├── frontend/                  # React фронтенд
│   ├── src/                  # React компоненти
│   │   ├── components/       # UI компоненти
│   │   ├── contexts/         # React контексти
│   │   ├── services/         # API сервіси
│   │   ├── types/            # TypeScript типи
│   │   └── App.tsx           # Головний компонент
│   ├── package.json          # Node.js залежності
│   ├── tailwind.config.js    # Tailwind CSS конфігурація
│   └── README.md             # Документація фронтенду
└── README.md                 # Головна документація
```

## 🔧 API Endpoints

### Авторизація
- `POST /register` - реєстрація користувача
- `POST /login` - авторизація
- `POST /logout` - вихід з системи

### Користувачі
- `GET /users` - список всіх користувачів
- `GET /me` - інформація про поточного користувача

### Чати
- `POST /chats` - створення приватного чату
- `GET /chats` - список чатів користувача
- `GET /chats/{chat_id}/participants` - учасники чату

### Повідомлення
- `POST /chats/{chat_id}/messages` - відправлення повідомлення
- `GET /chats/{chat_id}/messages` - отримання повідомлень
- `PUT /messages/{message_id}` - редагування повідомлення
- `DELETE /messages/{message_id}` - видалення повідомлення

### Файли
- `POST /messages/{message_id}/files` - завантаження файлу
- `GET /files/{file_id}` - завантаження файлу

## 🎨 Frontend Особливості

### React + TypeScript
- **TypeScript** для типобезпеки
- **React Hooks** для управління станом
- **Context API** для глобального стану
- **Functional Components** з сучасним синтаксисом

### Tailwind CSS
- **Utility-first** підхід до стилізації
- **Responsive дизайн** для всіх пристроїв
- **Custom animations** та transitions
- **Dark/Light теми** (готові до реалізації)

### UI/UX
- **Сучасний дизайн** з Material Design принципами
- **Responsive layout** для мобільних пристроїв
- **Smooth animations** та transitions
- **Accessibility** стандарти

## 🗄️ База даних

### Основні таблиці:
- **users** - користувачі системи
- **chats** - приватні чати між користувачами
- **messages** - повідомлення в чатах
- **chat_members** - учасники чатів
- **file_attachments** - прикріплені файли
- **blacklisted_tokens** - відкликані JWT токени

## 🔒 Безпека

- **JWT токени** з терміном дії 30 хвилин
- **Хешування паролів** з використанням bcrypt
- **Перевірка прав доступу** до чатів та повідомлень
- **Blacklist токенів** при виході з системи
- **CORS налаштування** для фронтенду

## 🚧 TODO

### Backend
- [ ] WebSocket для real-time чату
- [ ] Push-сповіщення
- [ ] Файлове сховище (AWS S3, MinIO)
- [ ] Rate limiting
- [ ] Логування та моніторинг

### Frontend
- [ ] Real-time оновлення повідомлень
- [ ] Drag & Drop для файлів
- [ ] Темна/світла тема
- [ ] PWA функціональність
- [ ] Unit тести (Jest + React Testing Library)

## 🛠️ Технології

### Backend
- **FastAPI** - сучасний веб-фреймворк
- **SQLAlchemy** - ORM для бази даних
- **PostgreSQL** - реляційна база даних
- **JWT** - авторизація
- **Pydantic** - валідація даних

### Frontend
- **React 18** - UI бібліотека
- **TypeScript** - типізована JavaScript
- **Tailwind CSS** - utility-first CSS фреймворк
- **React Context** - управління станом
- **Fetch API** - HTTP клієнт

## 📱 Використання

### Реєстрація та авторизація
1. Відкрийте **http://localhost:3000**
2. Зареєструйтеся з унікальним email та username
3. Увійдіть в систему

### Створення чату
1. У списку користувачів натисніть на ім'я користувача
2. Автоматично створиться приватний чат
3. Почніть спілкування!

### Функції месенджера
- **Відправлення повідомлень** - введіть текст та натисніть Enter
- **Редагування** - натисніть на повідомлення (TODO)
- **Видалення** - видалення власних повідомлень (TODO)
- **Файли** - прикріплення файлів (TODO)

## 🚀 Розгортання

### Backend (Production)
```bash
# Збірка Docker образу
docker build -t meduzzen-backend .

# Запуск контейнера
docker run -p 8000:8000 meduzzen-backend
```

### Frontend (Production)
```bash
# Збірка для продакшену
npm run build

# Розгортання на статичному хостингу
# (Netlify, Vercel, GitHub Pages)
```