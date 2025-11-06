import React from 'react';
import useWindowSize from '../hooks/useWindowSize';

interface ContextSource {
  source?: string;
  context?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  contextSources?: ContextSource[];
  createdAt: string;
}

interface MessageListProps {
  messages: ChatMessage[];
  responseTime: number | null;
  isLoading: boolean;
  renderMarkdown: (content: string) => React.ReactNode;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  responseTime,
  isLoading,
  renderMarkdown,
}) => {
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;
  const lastAssistantMessageId = [...messages]
    .reverse()
    .find((message) => message.role === 'assistant')?.id;

  return (
    <div className="space-y-4">
      {messages.map((message) => {
        const isUser = message.role === 'user';
        return (
          <div key={message.id} className="space-y-2">
            <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`${
                  isUser
                    ? 'bg-blue-100 dark:bg-blue-900'
                    : 'bg-white dark:bg-gray-800 shadow'
                } p-3 rounded-3xl ${
                  isMobile ? 'max-w-[90%]' : 'max-w-[70%]'
                } break-words whitespace-pre-wrap`}
              >
                {isUser ? (
                  message.content
                ) : (
                  <div className="space-y-2">
                    <div className="break-words overflow-x-auto">
                      {renderMarkdown(message.content)}
                    </div>
                    {responseTime && message.id === lastAssistantMessageId && (
                      <div className="text-sm text-gray-500">
                        Response time: {responseTime}ms
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
      {isLoading && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
