'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  PaperAirplaneIcon,
  SunIcon,
  MoonIcon,
  BoltIcon,
  Bars3Icon,
} from '@heroicons/react/24/solid';
import ChatHistory from '../components/ChatHistory';
import MessageList, { ChatMessage } from '../components/MessageList';
import SourceList from '../components/SourceList';
import SuggestedQuestions from '../components/SuggestedQuestions';
import { useTheme } from 'next-themes';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import useWindowSize from '../hooks/useWindowSize';
import './globals.css';
import '../styles/markdown-table.css';
import CopyButton from '../components/CopyButton';

const API_BASE_URL = process.env.NEXT_PUBLIC_PROXY_ENDPOINT;

interface ContextSource {
  source?: string;
  context?: string;
}

interface ConversationListItem {
  uuid: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

interface ConversationMessageResponse {
  uuid: string;
  conversation_uuid: string;
  role: 'user' | 'assistant';
  content: string;
  context_sources?: unknown;
  tools?: string[] | null;
  created_at: string;
}

interface ConversationDetailResponse extends ConversationListItem {
  messages: ConversationMessageResponse[];
}

interface AgentResponsePayload {
  response: string;
  context_sources?: unknown;
  tools?: string[];
}

interface ConversationSummary {
  sessionId: string;
  title: string;
  updatedAt: string;
}

const mapConversationSummary = (
  item: ConversationListItem
): ConversationSummary => ({
  sessionId: item.uuid,
  title: item.title ?? 'Untitled conversation',
  updatedAt: item.updated_at,
});

const normalizeContextSources = (raw: unknown): ContextSource[] => {
  const normalizeEntry = (entry: unknown): ContextSource[] => {
    if (!entry) {
      return [];
    }

    if (typeof entry === 'string') {
      return [{ source: entry, context: '' }];
    }

    if (Array.isArray(entry)) {
      return entry.flatMap((nested) => normalizeEntry(nested));
    }

    if (typeof entry === 'object') {
      const record = entry as Record<string, unknown>;

      if (Array.isArray(record.sources)) {
        return record.sources.flatMap((nested) => normalizeEntry(nested));
      }

      const sourceCandidate =
        (typeof record.source === 'string' && record.source) ||
        (typeof record.url === 'string' && record.url) ||
        (typeof record.href === 'string' && record.href) ||
        '';

      const contextCandidate =
        typeof record.context === 'string'
          ? record.context
          : typeof record.snippet === 'string'
            ? record.snippet
            : '';

      if (!sourceCandidate && !contextCandidate) {
        return Object.values(record).flatMap((nested) =>
          normalizeEntry(nested)
        );
      }

      return [
        {
          source: sourceCandidate,
          context: contextCandidate,
        },
      ];
    }

    return [];
  };

  return normalizeEntry(raw);
};

export default function Home() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentTitle, setCurrentTitle] = useState<string>(
    'Untitled conversation'
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const { theme, setTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  const ensureApiBase = useCallback(() => {
    if (!API_BASE_URL) {
      throw new Error(
        'NEXT_PUBLIC_PROXY_ENDPOINT is not defined. Set it to your backend URL.'
      );
    }
    return API_BASE_URL;
  }, []);

  const fetchConversations = useCallback(async () => {
    try {
      const baseUrl = ensureApiBase();
      const response = await fetch(`${baseUrl}/conversations`);

      if (!response.ok) {
        throw new Error(`Failed to fetch conversations (${response.status}).`);
      }

      const data: ConversationListItem[] = await response.json();
      setConversations(data.map(mapConversationSummary));
    } catch (fetchError) {
      console.error('Failed to load conversations:', fetchError);
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : 'Unable to load conversations.'
      );
    }
  }, [ensureApiBase]);

  const loadConversation = useCallback(
    async (sessionId: string) => {
      if (!sessionId) {
        throw new Error('Conversation identifier is missing.');
      }

      try {
        const baseUrl = ensureApiBase();
        const response = await fetch(`${baseUrl}/conversations/${sessionId}`);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Conversation not found.');
          }
          throw new Error(`Failed to load conversation (${response.status}).`);
        }

        const data: ConversationDetailResponse = await response.json();

        setCurrentSessionId(data.uuid);
        setCurrentTitle(data.title ?? 'Untitled conversation');
        setMessages(
          data.messages.map((message) => ({
            id: message.uuid,
            role: message.role,
            content: message.content,
            contextSources: normalizeContextSources(message.context_sources),
            createdAt: message.created_at,
          }))
        );
        setError(null);
      } catch (conversationError) {
        console.error('Failed to load conversation:', conversationError);
        setError(
          conversationError instanceof Error
            ? conversationError.message
            : 'Unable to load the selected conversation.'
        );
      }
    },
    [ensureApiBase]
  );

  const createConversation = useCallback(async () => {
    const baseUrl = ensureApiBase();
    const response = await fetch(`${baseUrl}/conversations`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to create conversation (${response.status}): ${
          errorText || response.statusText
        }`
      );
    }

    const data: ConversationDetailResponse = await response.json();
    const summary = mapConversationSummary(data);

    setConversations((prev) => [
      summary,
      ...prev.filter(
        (conversation) => conversation.sessionId !== summary.sessionId
      ),
    ]);
    setCurrentSessionId(summary.sessionId);
    setCurrentTitle(summary.title ?? 'Untitled conversation');
    setMessages([]);
    setError(null);

    return summary;
  }, [ensureApiBase]);

  const sendMessage = useCallback(
    async (prompt: string) => {
      const trimmedPrompt = prompt.trim();
      if (!trimmedPrompt) {
        return;
      }

      let optimisticMessage: ChatMessage | null = null;

      try {
        setIsLoading(true);
        setError(null);

        let sessionId = currentSessionId;
        if (!sessionId) {
          const conversation = await createConversation();
          sessionId = conversation.sessionId;
        }

        if (!sessionId) {
          throw new Error('Unable to determine the conversation identifier.');
        }

        optimisticMessage = {
          id: `local-${Date.now()}`,
          role: 'user',
          content: trimmedPrompt,
          contextSources: [],
          createdAt: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, optimisticMessage as ChatMessage]);
        setInput('');

        const baseUrl = ensureApiBase();
        const startTime = Date.now();
        const response = await fetch(
          `${baseUrl}/conversations/agent-retriever`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: trimmedPrompt,
              conversation_uuid: sessionId,
              list_context: true,
              list_sources: true,
            }),
          }
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `Agent request failed (${response.status}): ${
              errorText || response.statusText
            }`
          );
        }

        const data: AgentResponsePayload = await response.json();
        if (!data.response) {
          throw new Error('No response received from the assistant.');
        }

        const endTime = Date.now();
        setResponseTime(endTime - startTime);

        await Promise.all([loadConversation(sessionId), fetchConversations()]);
      } catch (sendError) {
        console.error('Error sending message:', sendError);
        if (optimisticMessage) {
          setMessages((prev) =>
            prev.filter((message) => message.id !== optimisticMessage?.id)
          );
        }
        if (
          sendError instanceof TypeError &&
          sendError.message === 'Failed to fetch'
        ) {
          setError(
            'Failed to reach the backend. Verify NEXT_PUBLIC_PROXY_ENDPOINT and CORS settings.'
          );
        } else {
          setError(
            sendError instanceof Error
              ? sendError.message
              : 'Failed to send the message.'
          );
        }
      } finally {
        setIsLoading(false);
      }
    },
    [
      currentSessionId,
      createConversation,
      ensureApiBase,
      fetchConversations,
      loadConversation,
    ]
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setIsSidebarOpen(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendMessage(input);
  };

  const handleNewConversation = async () => {
    try {
      await createConversation();
      await fetchConversations();
    } catch (newConversationError) {
      console.error(
        'Unable to create a new conversation:',
        newConversationError
      );
      setError(
        newConversationError instanceof Error
          ? newConversationError.message
          : 'Unable to create a new conversation.'
      );
    }
  };

  const handleSelectConversation = async (sessionId: string) => {
    await loadConversation(sessionId);
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteConversation = async (sessionId: string) => {
    const conversation = conversations.find((c) => c.sessionId === sessionId);
    const confirmed = window.confirm(
      `Delete "${conversation?.title || 'Untitled conversation'}"? This cannot be undone.`
    );

    if (!confirmed) return;

    try {
      const baseUrl = ensureApiBase();
      const response = await fetch(`${baseUrl}/conversations/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Conversation not found.');
        }
        throw new Error(`Failed to delete conversation (${response.status}).`);
      }

      setConversations((prev) =>
        prev.filter((conversation) => conversation.sessionId !== sessionId)
      );

      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
        setCurrentTitle('Untitled conversation');
      }
    } catch (deleteError) {
      console.error('Failed to delete conversation:', deleteError);
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : 'Unable to delete the selected conversation.'
      );
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    void sendMessage(question);
  };

  const latestUserMessage = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'user'),
    [messages]
  );

  const latestAssistantMessage = useMemo(
    () =>
      [...messages].reverse().find((message) => message.role === 'assistant'),
    [messages]
  );

  const latestSources = latestAssistantMessage?.contextSources || [];

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {(isSidebarOpen || !isMobile) && (
        <div
          className={`${
            isMobile ? 'absolute z-10 h-full' : 'relative'
          } bg-white dark:bg-gray-800 w-64`}
        >
          <ChatHistory
            conversations={conversations}
            activeSessionId={currentSessionId}
            onNewConversation={handleNewConversation}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
            isMobile={isMobile}
            onClose={handleCloseSidebar}
          />
        </div>
      )}
      <div className="flex-1 flex flex-col">
        <div className="bg-white dark:bg-gray-800 p-2 sm:p-3 md:p-4 shadow-md rounded-b-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 md:space-x-4">
              {isMobile && (
                <button
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="mr-2 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
                >
                  <Bars3Icon className="h-6 w-6" />
                </button>
              )}
              <BoltIcon className="h-8 w-8 text-blue-500 mr-2" />
              <div>
                <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                  ORAssistant
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {currentTitle}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                const nextTheme = theme === 'dark' ? 'light' : 'dark';
                setTheme(nextTheme);
                localStorage.setItem('theme', nextTheme);
              }}
              className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              {!mounted ? (
                <div className="h-6 w-6" />
              ) : theme === 'dark' ? (
                <SunIcon className="h-6 w-6 text-yellow-500" />
              ) : (
                <MoonIcon className="h-6 w-6 text-gray-500" />
              )}
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {error && (
            <div
              className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative animate-fade-in"
              role="alert"
            >
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          {messages.length > 0 && (
            <div className="animate-fade-in">
              <MessageList
                messages={messages}
                responseTime={responseTime}
                isLoading={isLoading}
                renderMarkdown={(content) => (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({
                        node,
                        inline,
                        className,
                        children,
                        ...props
                      }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <div className="relative group">
                            <SyntaxHighlighter
                              style={tomorrow}
                              language={match[1]}
                              PreTag="div"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                            <CopyButton text={String(children)} />
                          </div>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {content}
                  </ReactMarkdown>
                )}
              />
            </div>
          )}
          {latestSources.length > 0 && (
            <div className="animate-fade-in">
              <SourceList sources={latestSources} />
            </div>
          )}
          <SuggestedQuestions
            onSelectQuestion={handleSuggestedQuestion}
            latestQuestion={latestUserMessage?.content || ''}
            assistantAnswer={latestAssistantMessage?.content || ''}
          />
        </div>
        <form
          onSubmit={handleSubmit}
          className="p-4 bg-white dark:bg-gray-800 shadow-lg rounded-t-lg transition-colors duration-200"
        >
          <div className="flex items-center">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="flex-1 p-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-colors duration-200 disabled:opacity-50"
              placeholder="Type your message..."
              disabled={isLoading}
            />
            <button
              type="submit"
              className="bg-blue-500 text-white p-2 rounded-r-lg hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? (
                <svg
                  className="animate-spin h-5 w-5 text-white"
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
                <PaperAirplaneIcon className="h-6 w-6" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
