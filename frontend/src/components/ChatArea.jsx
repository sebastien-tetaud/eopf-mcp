import React, { useEffect, useRef } from 'react';
import { useChatContext } from '../context/ChatContext';
import { Message } from './Message';
import { ChatInput } from './ChatInput';

export const ChatArea = () => {
  const { currentSession, streamingContent, isStreaming, sendMessage } = useChatContext();
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, streamingContent]);

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#f5f5f0]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {!currentSession ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-[#706b5e] max-w-2xl px-4">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-[#a39d8d]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <h2 className="text-xl font-medium text-[#2c2923] mb-2">
                Welcome to Ask EOPF
              </h2>
              <p className="text-sm mb-6">
                Select a chat from the sidebar or create a new one to start chatting with
                the MCP-powered assistant.
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-8">
            {/* Messages */}
            {currentSession.messages && currentSession.messages.length > 0 ? (
              currentSession.messages.map((message, idx) => {
                // Find the previous user message for context
                let userMessage = null;
                for (let i = idx - 1; i >= 0; i--) {
                  if (currentSession.messages[i].role === 'user') {
                    userMessage = currentSession.messages[i];
                    break;
                  }
                }
                return <Message key={idx} message={message} userMessage={userMessage} />;
              })
            ) : (
              <div className="text-center py-8">
                <p className="text-[#706b5e] mb-6">No messages yet. Try one of these example queries:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {[
                    "List all available collections",
                    "Find Sentinel-2 L2A data over Paris from March 2026",
                    "Search for Sentinel-2 L2A in the Alps region",
                    "What Sentinel-2 L2A data is available for Barcelona?",
                  ].map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(example)}
                      className="text-left p-3 bg-white border border-[#d4d0c8] rounded-lg hover:border-[#a9754f] hover:bg-[#fff9e6] transition-colors text-sm text-[#2c2923]"
                    >
                      <span className="text-[#a9754f] mr-2">→</span>
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Streaming Message */}
            {isStreaming && streamingContent && (
              <div className="mb-8">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded bg-[#a9754f] flex items-center justify-center">
                    <span className="text-white text-sm font-medium">AI</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[#2c2923] whitespace-pre-wrap break-words">
                      {streamingContent}
                      <span className="inline-block w-1.5 h-4 bg-[#a9754f] ml-1 animate-pulse"></span>
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <ChatInput />
    </div>
  );
};
