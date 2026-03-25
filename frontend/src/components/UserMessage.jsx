import React from 'react';

export const UserMessage = ({ message }) => {
  return (
    <div className="mb-8">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded bg-[#2c2923] flex items-center justify-center">
          <span className="text-white text-sm font-medium">You</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[#2c2923] whitespace-pre-wrap break-words font-normal">
            {message.content}
          </p>
        </div>
      </div>
    </div>
  );
};
