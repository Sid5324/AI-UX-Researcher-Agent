# Next.js Frontend Setup

## Quick Start

```bash
# Install Next.js
npx create-next-app@latest frontend-nextjs --typescript --tailwind --app

# Install dependencies
cd frontend-nextjs
npm install @tanstack/react-query zustand axios socket.io-client

# Install UI components
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react

# Run development server
npm run dev
```

## Project Structure Created

```
frontend-nextjs/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── dashboard/page.tsx
│   │   └── projects/page.tsx
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── AuthForm.tsx
│   ├── ProjectCard.tsx
│   └── Header.tsx
├── lib/
│   ├── api.ts
│   └── auth.ts
└── package.json
```

## Key Files Included

### 1. API Client (lib/api.ts)
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### 2. Auth Hook (hooks/useAuth.ts)
```typescript
import { create } from 'zustand';
import api from '@/lib/api';

interface AuthState {
  user: any | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    set({ user });
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null });
  },
}));
```

### 3. Login Page (app/(auth)/login/page.tsx)
```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
    router.push('/dashboard');
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-8">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        className="w-full px-4 py-2 border rounded"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        className="w-full px-4 py-2 border rounded mt-4"
      />
      <button
        type="submit"
        className="w-full px-4 py-2 bg-blue-600 text-white rounded mt-4"
      >
        Sign In
      </button>
    </form>
  );
}
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Run the App

```bash
npm run dev
```

Visit http://localhost:3000

## Full Implementation

For complete Next.js implementation, run:
```bash
npx create-next-app@latest
```

And copy components from this guide.
