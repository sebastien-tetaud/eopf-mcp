/**
 * API client for communicating with the FastAPI backend
 */

const API_BASE = '/api';

export const api = {
  /**
   * List all sessions
   */
  async listSessions(limit = 50) {
    const response = await fetch(`${API_BASE}/sessions?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch sessions');
    return response.json();
  },

  /**
   * Create a new session
   */
  async createSession(title = null) {
    const response = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });
    if (!response.ok) throw new Error('Failed to create session');
    return response.json();
  },

  /**
   * Get a specific session
   */
  async getSession(sessionId) {
    const response = await fetch(`${API_BASE}/sessions/${sessionId}`);
    if (!response.ok) throw new Error('Session not found');
    return response.json();
  },

  /**
   * Delete a session
   */
  async deleteSession(sessionId) {
    const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete session');
    return response.json();
  },

  /**
   * Send a message
   */
  async sendMessage(sessionId, message) {
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  },

  /**
   * Subscribe to SSE stream for a session
   * Returns an EventSource instance
   */
  createEventSource(sessionId) {
    return new EventSource(`${API_BASE}/chat/stream/${sessionId}`);
  },
};
