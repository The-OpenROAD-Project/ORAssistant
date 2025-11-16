import { useState, useEffect, useCallback } from 'react';
import useWindowSize from '../hooks/useWindowSize';

interface SuggestedQuestionsProps {
  onSelectQuestion: (question: string) => void;
  latestQuestion: string;
  assistantAnswer: string;
}

const CHAT_ENDPOINT = process.env.NEXT_PUBLIC_PROXY_ENDPOINT;

export default function SuggestedQuestions({
  onSelectQuestion,
  latestQuestion,
  assistantAnswer,
}: SuggestedQuestionsProps) {
  const [questions, setQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  const fetchSuggestedQuestions = useCallback(async () => {
    // Show default questions if there's no conversation yet
    if (!latestQuestion || !assistantAnswer) {
      setQuestions([
        'How do I get started with OpenROAD?',
        'What are the main features of OpenROAD?',
        'How do I install OpenROAD-flow-scripts?',
        'What is the OpenROAD flow?',
      ]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${CHAT_ENDPOINT}/helpers/suggestedQuestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          latest_question: latestQuestion,
          assistant_answer: assistantAnswer,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setQuestions(data.suggested_questions || []);
    } catch (error) {
      console.error('Error fetching suggested questions:', error);
      setQuestions([]);
    } finally {
      setIsLoading(false);
    }
  }, [latestQuestion, assistantAnswer]);

  useEffect(() => {
    fetchSuggestedQuestions();
  }, [fetchSuggestedQuestions]);

  return (
    <div
      className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow transition-colors duration-200 ${
        isMobile ? 'max-w-full' : 'max-w-[90%]'
      }`}
    >
      <h3 className="font-bold mb-2 text-gray-800 dark:text-white">
        Suggested Questions:
      </h3>
      {isLoading ? (
        <div className="flex justify-center items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
      ) : (
        <ul className="space-y-2">
          {questions.map((question, index) => (
            <li
              key={index}
              onClick={() => onSelectQuestion(question)}
              className="bg-gray-100 dark:bg-gray-700 p-2 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-800 dark:text-white transition-colors duration-200 break-words"
            >
              {question}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
