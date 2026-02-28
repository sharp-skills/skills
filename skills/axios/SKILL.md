---
name: axios
description: "Make HTTP requests in Node.js and browsers using Axios. Use when asked to: fetch data from an API with Axios, add request interceptors, handle Axios errors, set auth headers, configure timeouts, cancel requests, upload files, or create a reusable Axios instance."
license: Apache-2.0
compatibility:
  - node >= 14
  - browser: modern
metadata:
  author: SharpSkills
  version: 1.1.0
  category: development
  tags: [axios, http, rest-api, javascript, typescript, requests, interceptors, nodejs]
---

# Axios

Axios is a promise-based HTTP client for Node.js and browsers. It automatically transforms JSON, supports request/response interceptors, cancellation, and works in both server and client environments.

## Installation

```bash
npm install axios
```

## Quick Start

```typescript
import axios from 'axios';

const { data } = await axios.get('https://api.example.com/users');
console.log(data);
```

## When to Use
- "Make HTTP GET/POST/PUT/DELETE requests"
- "Add auth headers to all API requests"
- "Handle API errors globally with interceptors"
- "Upload files with Axios"
- "Set request timeout / cancel requests"
- "Create a reusable API client"

## Core Patterns

### Pattern 1: Reusable API Client Instance

```typescript
// lib/apiClient.ts
import axios, { AxiosError, AxiosInstance } from 'axios';

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.API_BASE_URL || 'https://api.example.com',
  timeout: 10_000, // 10s
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor — attach auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token') || process.env.API_TOKEN;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — normalize errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired — redirect to login or refresh
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Pattern 2: CRUD Requests

```typescript
import apiClient from './lib/apiClient';

interface User {
  id: number;
  name: string;
  email: string;
}

// GET — fetch with query params
const { data: users } = await apiClient.get<User[]>('/users', {
  params: { page: 1, limit: 20, role: 'admin' },
});

// POST — create
const { data: newUser } = await apiClient.post<User>('/users', {
  name: 'Alice',
  email: 'alice@example.com',
});

// PUT — full update
const { data: updated } = await apiClient.put<User>(`/users/${newUser.id}`, {
  name: 'Alice Smith',
  email: 'alice@example.com',
});

// PATCH — partial update
await apiClient.patch(`/users/${newUser.id}`, { name: 'Alice Johnson' });

// DELETE
await apiClient.delete(`/users/${newUser.id}`);
```

### Pattern 3: Error Handling

```typescript
import axios, { AxiosError } from 'axios';

interface ApiError {
  message: string;
  code: string;
}

async function fetchUser(id: number) {
  try {
    const { data } = await apiClient.get<User>(`/users/${id}`);
    return { data, error: null };
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const error = err as AxiosError<ApiError>;

      if (error.response) {
        // Server responded with 4xx / 5xx
        console.error(`API Error ${error.response.status}:`, error.response.data?.message);
        return { data: null, error: error.response.data };
      } else if (error.request) {
        // Request sent but no response (timeout, network down)
        console.error('Network error — no response received');
        return { data: null, error: { message: 'Network error', code: 'NETWORK_ERROR' } };
      }
    }
    // Non-Axios error
    throw err;
  }
}
```

### Pattern 4: File Upload (multipart/form-data)

```typescript
import axios from 'axios';

async function uploadFile(file: File, onProgress?: (pct: number) => void) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', 'documents');

  const { data } = await apiClient.post('/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress?.(pct);
      }
    },
  });

  return data; // { url: 'https://cdn.example.com/file.pdf' }
}
```

### Pattern 5: Retry with Exponential Backoff

```typescript
import axios from 'axios';

async function fetchWithRetry<T>(
  url: string,
  retries = 3,
  delayMs = 500,
): Promise<T> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const { data } = await apiClient.get<T>(url);
      return data;
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status && err.response.status < 500) {
        throw err; // 4xx — don't retry client errors
      }
      if (attempt === retries) throw err;
      await new Promise(r => setTimeout(r, delayMs * 2 ** (attempt - 1)));
    }
  }
  throw new Error('Max retries exceeded');
}

// Usage
const user = await fetchWithRetry<User>('/users/1', 3, 500);
```

### Pattern 6: Request Cancellation (AbortController)

```typescript
// React — cancel on component unmount
import { useEffect, useState } from 'react';
import apiClient from './lib/apiClient';

function useUsers() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const controller = new AbortController();

    apiClient.get('/users', { signal: controller.signal })
      .then(({ data }) => setUsers(data))
      .catch((err) => {
        if (axios.isCancel(err)) return; // ignore cancellations
        console.error(err);
      });

    return () => controller.abort(); // cancel on unmount
  }, []);

  return users;
}
```

## Production Notes

1. **Always use named instances, not the global `axios`** — `axios.create()` gives you isolated config per service. Mixing base URLs and auth in the global instance causes hard-to-debug bugs.
2. **`axios.isAxiosError(err)` before accessing `.response`** — TypeScript narrows the error type. Accessing `.response` on a non-Axios error throws.
3. **Set `timeout`** — Default is `0` (infinite). A hung upstream can block Node.js event loop workers indefinitely. Set 5–30s depending on the endpoint.
4. **Don't use `Content-Type: multipart/form-data` manually for uploads** — Let Axios (and FormData) set it automatically — they include the required `boundary` parameter that browsers strip if you override the header.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `Network Error` with no status | CORS blocked or server not running | Check browser console for CORS error; verify server URL |
| Response is `undefined` | Destructuring `.data` from failed catch branch | Use `axios.isAxiosError()` check before accessing response |
| File upload fails with `400 Bad Request` | Manual `Content-Type: multipart/form-data` header without boundary | Remove manual `Content-Type` header; let FormData set it |
| All requests return `401` after token refresh | Interceptor not re-attaching new token | In response interceptor, retry original request with new token |
| Timeout doesn't trigger | `timeout` not set on instance | Set `timeout: 10000` in `axios.create()` options |
| Request sent twice | Strict Mode double-invoke in React dev | Normal in dev; check network tab in production |

## Pre-Deploy Checklist
- [ ] `axios.create()` instance used (not global `axios`)
- [ ] `timeout` set (recommended: 10s for most APIs)
- [ ] Auth interceptor attaches token from secure storage
- [ ] Error interceptor handles 401 (token expiry) globally
- [ ] Retry logic for 5xx / network errors on critical paths
- [ ] Request cancellation on React component unmount to prevent state updates

## Resources
- Docs: https://axios-http.com/docs/intro
- GitHub: https://github.com/axios/axios
- Interceptors: https://axios-http.com/docs/interceptors
