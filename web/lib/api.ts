const API_BASE_URL = 'http://localhost:8000';

// Types
export interface UserSignup {
  username: string;
  name: string;
  age: number;
  email: string;
  password: string;
}

export interface UserOut {
  id: string;
  username: string;
  name: string;
  age: number;
  email: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface DocumentResponse {
  document_id: string;
  filename: string;
  status: string;
}

export interface QARequest {
  document_id: string;
  question: string;
  top_k?: number;
}

export interface QAResponse {
  answer: string;
  contexts: string[];
}

export interface DocumentStatusResp {
  document_id: string;
  status: string;
  error?: string | null;
  chunks_count?: number;
}

// Auth helpers
export const setToken = (token: string) => {
  localStorage.setItem('access_token', token);
};

export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const removeToken = () => {
  localStorage.removeItem('access_token');
};

async function handleNonOk(resp: Response) {
  try {
    const body = await resp.json();
    if (body?.detail) throw new Error(body.detail);
    if (body?.message) throw new Error(body.message);
    throw new Error(JSON.stringify(body));
  } catch {
    throw new Error(`HTTP ${resp.status}`);
  }
}

export const api = {
  // Auth
  signup: async (data: UserSignup): Promise<UserOut> => {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) await handleNonOk(response);
    return response.json();
  },

  login: async (email: string, password: string): Promise<Token> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) await handleNonOk(response);

    const json = await response.json();
    setToken(json.access_token);
    return json;
  },

  // RAG upload
  uploadDocument: async (file: File): Promise<DocumentResponse> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!resp.ok) await handleNonOk(resp);
    return resp.json();
  },

  // Summarize
  summarizeFile: async (file: File): Promise<{ filename: string; summary: string }> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch(`${API_BASE_URL}/summarize`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!resp.ok) await handleNonOk(resp);
    return resp.json();
  },

  // Ask question
  askQuestion: async (data: QARequest): Promise<QAResponse> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const resp = await fetch(`${API_BASE_URL}/qa/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!resp.ok) await handleNonOk(resp);
    return resp.json();
  },

  simplifyFile: async (file: File): Promise<{ filename: string; simplified_text: string }> => {
  const token = getToken();
  if (!token) throw new Error('Not authenticated');

  const formData = new FormData();
  formData.append('file', file);

  const resp = await fetch(`${API_BASE_URL}/simplify`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!resp.ok) await handleNonOk(resp);
  return resp.json();
},

simplifyText: async (text: string): Promise<{ simplified_text: string }> => {
  const token = getToken();
  if (!token) throw new Error('Not authenticated');

  const formData = new FormData();
  formData.append('text', text);

  const resp = await fetch(`${API_BASE_URL}/simplify`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!resp.ok) await handleNonOk(resp);
  return resp.json();
},

};
