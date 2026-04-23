const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * Helper function to call the local FastAPI backend.
 */
export async function fetchFromAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }

  // Not all endpoints might return JSON, but most will in this app
  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}

export const api = {
  getRepos: () => fetchFromAPI('/repos'),
  getJobs: () => fetchFromAPI('/agent/jobs'),
  triggerSync: (repoId: string) => fetchFromAPI(`/agent/trigger/${repoId}`, { method: 'POST' }),
  healthCheck: () => fetchFromAPI('/health'),
};
