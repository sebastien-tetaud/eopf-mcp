import React from 'react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';

export const Message = ({ message, userMessage }) => {
  if (message.role === 'user') {
    return <UserMessage message={message} />;
  }

  if (message.role === 'assistant') {
    return <AssistantMessage message={message} userMessage={userMessage} />;
  }

  return null;
};
