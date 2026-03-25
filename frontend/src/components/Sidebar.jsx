import { useNavigate, useLocation } from 'react-router-dom';
import { useChatContext } from '../context/ChatContext';
import { formatDistanceToNow } from 'date-fns';

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    createNewSession,
    deleteSession,
    loading,
  } = useChatContext();

  const handleNewChat = async () => {
    try {
      await createNewSession();
      // Navigate to chat view after creating new session
      if (location.pathname !== '/') {
        navigate('/');
      }
    } catch (err) {
      console.error('Failed to create new chat:', err);
    }
  };

  const handleSelectSession = (sessionId) => {
    setCurrentSessionId(sessionId);
    // Navigate to chat view when selecting a session
    if (location.pathname !== '/') {
      navigate('/');
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this session?')) {
      try {
        await deleteSession(sessionId);
      } catch (err) {
        console.error('Failed to delete session:', err);
      }
    }
  };

  return (
    <div className="w-64 bg-white border-r border-[#d4d0c8] flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-[#d4d0c8] space-y-2">
        <button
          onClick={handleNewChat}
          disabled={loading}
          className="w-full bg-[#a9754f] hover:bg-[#8b5f3f] text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          New Chat
        </button>

        <button
          onClick={() => navigate('/test-map')}
          className={`w-full font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 ${
            location.pathname === '/test-map'
              ? 'bg-[#2c2923] text-white'
              : 'bg-[#e8e6df] hover:bg-[#d4d0c8] text-[#2c2923]'
          }`}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          Test Map
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <div className="text-center text-[#706b5e] text-sm mt-4 px-2">
            No chat sessions yet. Click "New Chat" to start!
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors group relative ${
                  currentSessionId === session.id
                    ? 'bg-[#f5f5f0] text-[#2c2923] border border-[#a9754f]'
                    : 'hover:bg-[#f5f5f0] text-[#2c2923]'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">
                      {session.title}
                    </div>
                    <div className="text-xs text-[#706b5e] mt-1">
                      {formatDistanceToNow(new Date(session.updated_at), {
                        addSuffix: true,
                      })}
                    </div>
                    {session.messages && session.messages.length > 0 && (
                      <div className="text-xs text-[#a39d8d] mt-1">
                        {session.messages.length} message
                        {session.messages.length !== 1 ? 's' : ''}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-100 rounded"
                    title="Delete session"
                  >
                    <svg
                      className="w-4 h-4 text-red-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-[#d4d0c8] text-xs text-[#706b5e] text-center">
        ASK EOPF
      </div>
    </div>
  );
};
