import { PlusIcon, TrashIcon } from '@heroicons/react/24/solid';

interface ConversationSummary {
  sessionId: string;
  title: string | null;
  updatedAt: string;
}

interface ChatHistoryProps {
  conversations: ConversationSummary[];
  activeSessionId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (sessionId: string) => void;
  onDeleteConversation: (sessionId: string) => void;
  isMobile: boolean;
  onClose: () => void;
}

const truncateText = (text: string, maxLength: number) => {
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
};

const formatUpdatedAt = (updatedAt: string) => {
  try {
    return new Date(updatedAt).toLocaleString();
  } catch (error) {
    return updatedAt;
  }
};

export default function ChatHistory({
  conversations,
  activeSessionId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  isMobile,
  onClose,
}: ChatHistoryProps) {
  return (
    <div className="h-full bg-gray-200 dark:bg-gray-800 p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={onNewConversation}
          className="flex items-center justify-center bg-white dark:bg-gray-700 text-gray-800 dark:text-white font-semibold py-2 px-2 rounded-lg shadow hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200 w-10 h-10"
        >
          <PlusIcon className="h-6 w-6" />
        </button>
        <h2 className="text-xl font-bold text-gray-800 dark:text-white flex-grow text-center">
          Threads
        </h2>
        {isMobile && (
          <button
            onClick={onClose}
            className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
        )}
      </div>
      <div className="space-y-2">
        {conversations.map((conversation) => (
          <div
            key={conversation.sessionId}
            className={`bg-white dark:bg-gray-700 p-3 rounded-lg shadow cursor-pointer transition-colors duration-200 flex justify-between items-center ${
              conversation.sessionId === activeSessionId
                ? 'border-2 border-blue-400'
                : 'hover:bg-gray-100 dark:hover:bg-gray-600'
            }`}
          >
            <div
              onClick={() => onSelectConversation(conversation.sessionId)}
              className="flex-1 truncate"
            >
              <h3 className="font-semibold text-gray-800 dark:text-white">
                {truncateText(
                  conversation.title || 'Untitled conversation',
                  42
                )}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {formatUpdatedAt(conversation.updatedAt)}
              </p>
            </div>
            <button
              onClick={() => onDeleteConversation(conversation.sessionId)}
              className="text-gray-500 hover:text-red-500 transition-colors duration-200"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
