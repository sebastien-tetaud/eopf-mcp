import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';

const ChatContext = createContext(null);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load current session when ID changes
  useEffect(() => {
    if (currentSessionId) {
      loadSession(currentSessionId);
    } else {
      setCurrentSession(null);
    }
  }, [currentSessionId]);

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listSessions();
      setSessions(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSession = useCallback(async (sessionId) => {
    try {
      const data = await api.getSession(sessionId);
      setCurrentSession(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load session:', err);
    }
  }, []);

  const createNewSession = useCallback(async (title = null) => {
    try {
      setLoading(true);
      const newSession = await api.createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setError(null);
      return newSession;
    } catch (err) {
      setError(err.message);
      console.error('Failed to create session:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteSession = useCallback(async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setCurrentSession(null);
      }
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Failed to delete session:', err);
      throw err;
    }
  }, [currentSessionId]);

  const sendMessage = useCallback(async (message) => {
    if (!currentSessionId) {
      throw new Error('No session selected');
    }

    try {
      // Send message (adds to session)
      await api.sendMessage(currentSessionId, message);

      // Reload session to get the user message
      await loadSession(currentSessionId);

      // Start streaming
      setIsStreaming(true);
      setStreamingContent('');

      const eventSource = api.createEventSource(currentSessionId);

      eventSource.addEventListener('message_start', (e) => {
        console.log('Stream started:', e.data);
      });

      eventSource.addEventListener('content_delta', (e) => {
        const data = JSON.parse(e.data);
        setStreamingContent((prev) => prev + (data.data?.text || ''));
      });

      eventSource.addEventListener('tool_call', (e) => {
        const data = JSON.parse(e.data);
        console.log('Tool called:', data.data);
      });

      eventSource.addEventListener('tool_result', (e) => {
        const data = JSON.parse(e.data);
        console.log('Tool result:', data.data);
      });

      eventSource.addEventListener('message_end', async (e) => {
        console.log('Stream ended:', e.data);
        setIsStreaming(false);
        setStreamingContent('');
        eventSource.close();

        // Reload session to get the complete assistant message
        await loadSession(currentSessionId);
        await loadSessions(); // Update session list
      });

      eventSource.addEventListener('error', (e) => {
        console.error('Stream error:', e);
        const data = e.data ? JSON.parse(e.data) : { data: { message: 'Unknown error' } };
        setError(data.data?.message || 'Stream error');
        setIsStreaming(false);
        setStreamingContent('');
        eventSource.close();
      });

      eventSource.onerror = (e) => {
        console.error('EventSource error:', e);
        setError('Connection error');
        setIsStreaming(false);
        setStreamingContent('');
        eventSource.close();
      };

    } catch (err) {
      setError(err.message);
      console.error('Failed to send message:', err);
      throw err;
    }
  }, [currentSessionId, loadSession, loadSessions]);

  const value = {
    sessions,
    currentSessionId,
    currentSession,
    streamingContent,
    isStreaming,
    loading,
    error,
    setCurrentSessionId,
    createNewSession,
    deleteSession,
    sendMessage,
    loadSessions,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
