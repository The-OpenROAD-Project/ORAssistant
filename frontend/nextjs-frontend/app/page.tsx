'use client';
import { useState, useEffect } from 'react';
import {
  PaperAirplaneIcon,
  SunIcon,
  MoonIcon,
  BoltIcon,
  PlusIcon,
  TrashIcon,
  Bars3Icon,
  ArrowLeftIcon,
} from '@heroicons/react/24/solid';
import ChatHistory from '../components/ChatHistory';
import MessageList from '../components/MessageList';
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

const CHAT_ENDPOINT = process.env.NEXT_PUBLIC_PROXY_ENDPOINT;

interface Message {
  question: string;
  answer: string;
  sources: string[];
  timestamp: number;
}
interface Thread {
  id: string;
  title: string;
  messages: Message[];
  // suggestedQuestions: string[];
}

interface ApiResponse {
  response: string;
  sources: string[];
  context: string[];
}

export default function Home() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThread, setCurrentThread] = useState<Thread | null>(null);
  const [input, setInput] = useState('');
  const { theme, setTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  useEffect(() => {
    setIsSidebarOpen(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    const storedThreads = sessionStorage.getItem('chatThreads');
    if (storedThreads) {
      setThreads(JSON.parse(storedThreads));
    }
  }, []);

  useEffect(() => {
    console.log('Current theme:', theme);
  }, [theme]);

  useEffect(() => {
    setTheme('dark');
  }, [setTheme]); // Add setTheme to the dependency array

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (input.trim()) {
      setIsLoading(true);
      setError(null);
      const startTime = Date.now();

      try {
        // Get the last 4 messages from the current thread
        const lastFourMessages = currentThread
          ? currentThread.messages.slice(-4)
          : [];

        // Construct the chat history
        const chatHistory = lastFourMessages.map((msg) => ({
          User: msg.question,
          AI: msg.answer,
        }));

        if (!CHAT_ENDPOINT) {
          throw new Error('CHAT_ENDPOINT is not defined');
        }

        const response = await fetch(CHAT_ENDPOINT, {
          method: 'POST',
          headers: {
            accept: 'application/json',
            'Content-Type': 'application/json',
            Origin: window.location.origin,
          },
          body: JSON.stringify({
            query: input,
            list_context: true,
            list_sources: true,
            chat_history: chatHistory,
          }),
          mode: 'cors',
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `HTTP error! status: ${response.status}, message: ${errorText}`
          );
        }

        const data: ApiResponse = await response.json();
        const endTime = Date.now();
        setResponseTime(endTime - startTime);

        if (!data.response) {
          throw new Error('No answer received from the API');
        }

        const newMessage = {
          question: input,
          answer: data.response,
          sources: data.sources || [],
          timestamp: Date.now(),
        };
        const updatedThread = currentThread
          ? {
              ...currentThread,
              messages: [...currentThread.messages, newMessage],
              // suggestedQuestions: currentThread.suggestedQuestions,
            }
          : {
              id: Date.now().toString(),
              title: input,
              messages: [newMessage],
              // suggestedQuestions: [],
            };

        setCurrentThread(updatedThread);
        setThreads((prev) => {
          const updated = currentThread
            ? prev.map((t) => (t.id === currentThread.id ? updatedThread : t))
            : [updatedThread, ...prev];
          sessionStorage.setItem('chatThreads', JSON.stringify(updated));
          return updated;
        });
        setInput('');

        setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 100);
      } catch (error) {
        console.error('Error fetching response:', error);
        if (error instanceof Error) {
          if (error.message.includes('CORS')) {
            setError(
              'CORS error: The server is not configured to accept requests from this origin. Please contact the API administrator.'
            );
          } else {
            setError(error.message);
          }
        } else {
          setError('An unknown error occurred');
        }
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleNewChat = () => {
    setCurrentThread(null);
  };

  const handleSelectThread = (threadId: string) => {
    const selected = threads.find((t) => t.id === threadId);
    if (selected) setCurrentThread(selected);
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    handleSubmit({
      preventDefault: () => {},
    } as React.FormEvent<HTMLFormElement>);
  };

  const handleDeleteThread = (threadId: string) => {
    setThreads((prev) => {
      const updated = prev.filter((t) => t.id !== threadId);
      sessionStorage.setItem('chatThreads', JSON.stringify(updated));
      return updated;
    });
    if (currentThread?.id === threadId) {
      setCurrentThread(null);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {(isSidebarOpen || !isMobile) && (
        <div
          className={`${
            isMobile ? 'absolute z-10 h-full' : 'relative'
          } bg-white dark:bg-gray-800 w-64`}
        >
          <ChatHistory
            threads={threads}
            onNewChat={handleNewChat}
            onSelectThread={handleSelectThread}
            onDeleteThread={handleDeleteThread}
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
              <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                ORAssistant
              </h1>
            </div>
            <button
              onClick={() => {
                const newTheme = theme === 'dark' ? 'light' : 'dark';
                console.log('Switching theme to:', newTheme); // Add this line
                setTheme(newTheme);
                localStorage.setItem('theme', newTheme);
              }}
              className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              {theme === 'dark' ? (
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
          {currentThread && (
            <div className="animate-fade-in">
              <MessageList
                messages={currentThread.messages}
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
          {currentThread && currentThread.messages.length > 0 && (
            <div className="animate-fade-in">
              <SourceList
                sources={
                  currentThread.messages[currentThread.messages.length - 1]
                    .sources || []
                }
              />
            </div>
          )}
          <SuggestedQuestions
            onSelectQuestion={handleSuggestedQuestion}
            latestQuestion={
              currentThread?.messages[currentThread.messages.length - 1]
                ?.question || ''
            }
            assistantAnswer={
              currentThread?.messages[currentThread.messages.length - 1]
                ?.answer || ''
            }
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
              onChange={(e) => setInput(e.target.value)}
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
