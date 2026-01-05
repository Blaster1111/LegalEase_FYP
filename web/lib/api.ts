// lib/api.ts
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

interface QAHistory {
  question: string;
  answer: string;
  contexts: string[];
  timestamp: Date; 
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
  // Try JSON first
  try {
    const body = await resp.json();
    // common FastAPI error shape: { "detail": "..." } or custom
    if (body?.detail) throw new Error(body.detail);
    // if body has message property
    if (body?.message) throw new Error(body.message);
    // otherwise stringify the body
    throw new Error(JSON.stringify(body));
  } catch (jsonErr) {
    // If parsing JSON failed, read text
    try {
      const txt = await resp.text();
      throw new Error(txt || `HTTP ${resp.status}`);
    } catch (_) {
      throw new Error(`HTTP ${resp.status}`);
    }
  }
}

// API functions
export const api = {
  // Auth endpoints
  signup: async (data: UserSignup): Promise<UserOut> => {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }
    return response.json();
  },

  login: async (email: string, password: string): Promise<Token> => {
    const formData = new FormData();
    formData.append('username', email); // OAuth2 uses 'username' field
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
    const json = await response.json();
    setToken(json.access_token);
    return json;
  },

  // Document endpoints
  uploadDocument: async (file: File): Promise<DocumentResponse> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    return response.json();
  },

  // New: fetch list of user's documents
  getUserDocuments: async (): Promise<DocumentResponse[]> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const resp = await fetch(`${API_BASE_URL}/documents/list`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || 'Could not fetch documents');
    }
    return resp.json();
  },

  // New: fetch document status
  getDocumentStatus: async (document_id: string): Promise<DocumentStatusResp> => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const resp = await fetch(`${API_BASE_URL}/documents/status/${document_id}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || 'Could not fetch document status');
    }
    return resp.json();
  },

  // Fetch Q&A history for a document
getQAHistory: async (document_id: string): Promise<QAHistory[]> => {
  const token = getToken();
  if (!token) throw new Error('Not authenticated');

  const resp = await fetch(`${API_BASE_URL}/qa/history/${document_id}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!resp.ok) {
    await handleNonOk(resp);
  }

  return resp.json();
},


  // QA endpoints
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

    if (!resp.ok) {
      await handleNonOk(resp);
    }

    // OK
    return resp.json();
  },
};
