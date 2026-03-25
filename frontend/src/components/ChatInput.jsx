import React, { useState, useRef, useEffect } from 'react';
import { useChatContext } from '../context/ChatContext';

export const ChatInput = () => {
  const { sendMessage, isStreaming, currentSessionId } = useChatContext();
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!input.trim() || isSending || isStreaming || !currentSessionId) {
      return;
    }

    const messageToSend = input.trim();
    setInput('');
    setIsSending(true);

    try {
      await sendMessage(messageToSend);
    } catch (err) {
      console.error('Failed to send message:', err);
      // Restore input on error
      setInput(messageToSend);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isDisabled = isSending || isStreaming || !currentSessionId;

  return (
    <div className="border-t border-[#d4d0c8] bg-white p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="flex gap-2 items-center">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                currentSessionId
                  ? 'Reply to Ask EOPF ...'
                  : 'Select or create a session to start chatting'
              }
              disabled={isDisabled}
              className="w-full resize-none rounded-lg border border-[#d4d0c8] bg-white text-[#2c2923] px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#a9754f] focus:border-transparent disabled:bg-[#f5f5f0] disabled:cursor-not-allowed max-h-40 overflow-y-auto placeholder-[#a39d8d]"
              rows={1}
            />
          </div>

          <button
            type="submit"
            disabled={isDisabled || !input.trim()}
            className="bg-[#a9754f] hover:bg-[#8b5f3f] text-white p-2.5 rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            title="Send message"
          >
            {isSending || isStreaming ? (
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 10l7-7m0 0l7 7m-7-7v18"
                />
              </svg>
            )}
          </button>
        </div>

        {/* {!currentSessionId && (
          <div className="text-sm text-[#706b5e] mt-2 text-center">
            Create a new session or select an existing one to start chatting
          </div>
        )} */}
      </form>
    </div>
  );
};
