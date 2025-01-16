import React from "react";
import useWindowSize from "../hooks/useWindowSize";

interface Message {
  question: string;
  answer: string;
  sources: string[];
  timestamp: number;
}

interface MessageListProps {
  messages: Message[];
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

  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <div key={index} className="space-y-2">
          <div className="flex justify-end">
            <div
              className={`bg-blue-100 dark:bg-blue-900 p-3 rounded-3xl ${
                isMobile ? "max-w-[90%]" : "max-w-[70%]"
              } break-words`}
            >
              {message.question}
            </div>
          </div>
          <div
            className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow ${
              isMobile ? "max-w-full" : "max-w-[90%]"
            }`}
          >
            <div className="mb-2 break-words overflow-x-auto">
              {renderMarkdown(message.answer)}
            </div>
            {index === messages.length - 1 && responseTime && (
              <div className="text-sm text-gray-500">
                Response time: {responseTime}ms
              </div>
            )}
          </div>
        </div>
      ))}
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
