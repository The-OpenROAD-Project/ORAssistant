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
    <div className="space-y-2">
      {messages.map((message, index) => {
        const isUser = message.role === 'user';
        const prevMessage = index > 0 ? messages[index - 1] : null;
        const isNewConversationPair = isUser && prevMessage?.role === 'assistant';

        return (
          <div key={message.id} className={isNewConversationPair ? 'mt-8' : ''}>
            <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
              <div
                className={`${
                  isUser
                    ? 'bg-blue-500 dark:bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-md'
                } px-4 py-3 rounded-2xl ${
                  isMobile ? 'max-w-[90%]' : 'max-w-[75%]'
                } break-words`}
              >
                {isUser ? (
                  <div className="font-medium">{message.content}</div>
                ) : (
                  <div className="space-y-2">
                    <div className="break-words overflow-x-auto prose prose-sm dark:prose-invert max-w-none">
                      {renderMarkdown(message.content)}
                    </div>
                    {responseTime && message.id === lastAssistantMessageId && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
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
