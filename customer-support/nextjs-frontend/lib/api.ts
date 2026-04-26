const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIClient {
  private static get token(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  private static get headers(): HeadersInit {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const t = this.token;
    if (t) {
      h['Authorization'] = `Bearer ${t}`;
    }
    return h;
  }

  private static async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      throw new Error('Unauthorized');
    }
    if (response.status === 402) {
      throw new Error('Insufficient credits');
    }
    if (!response.ok) {
      let errorMsg = 'API request failed';
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorMsg;
      } catch (e) {
        // Ignore json parse error
      }
      throw new Error(errorMsg);
    }
    return response.json();
  }

  static async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    let url = `${BASE_URL}${path}`;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    const res = await fetch(url, {
      method: 'GET',
      headers: this.headers,
    });
    return this.handleResponse<T>(res);
  }

  static async post<T>(path: string, data?: any, isFormData = false): Promise<T> {
    const options: RequestInit = {
      method: 'POST',
      headers: isFormData ? {} : this.headers, // FormData handles its own Content-Type
    };

    if (this.token && isFormData) {
      options.headers = { Authorization: `Bearer ${this.token}` };
    }

    if (data) {
      options.body = isFormData ? data : JSON.stringify(data);
    }

    const res = await fetch(`${BASE_URL}${path}`, options);
    return this.handleResponse<T>(res);
  }

  static async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers: this.headers,
    });
    return this.handleResponse<T>(res);
  }
}
