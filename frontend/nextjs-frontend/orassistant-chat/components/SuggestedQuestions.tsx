import { useState, useEffect } from "react";
import useWindowSize from "../hooks/useWindowSize";

interface SuggestedQuestionsProps {
  onSelectQuestion: (question: string) => void;
  latestQuestion: string;
  assistantAnswer: string;
}

export default function SuggestedQuestions({
  onSelectQuestion,
  latestQuestion,
  assistantAnswer,
}: SuggestedQuestionsProps) {
  const [questions, setQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  useEffect(() => {
    fetchSuggestedQuestions();
  }, [latestQuestion, assistantAnswer]);

  const fetchSuggestedQuestions = async () => {
    setIsLoading(true);
    const prompt = `If the assistant answer has sufficient knowledge, use it to predict the next 3 suggested questions. Otherwise, strictly restrict to these topics: Given the list of topics related to OpenROAD, suggest 3 relevant questions strictly focused on any of the given topics.
    Getting Started with OpenROAD
    Building OpenROAD
    Getting Started with the OpenROAD Flow - OpenROAD-flow-scripts
    Tutorials
    Git Quickstart
    Man pages
    OpenROAD User Guide
    Database
    GUI
    Partition Management
    Restructure
    Floorplan Initialization
    Pin Placement
    Chip-level Connections
    Macro Placement
    Hierarchical Macro Placement
    Tapcell Insertion
    PDN Generation
    Global Placement
    Gate Resizing
    Detailed Placement
    Clock Tree Synthesis
    Global Routing
    Antenna Checker
    Detailed Routing
    Metal Fill
    Parasitics Extraction
    Messages Glossary
    Getting Involved
    Developer's Guide
    Coding Practices
    Logger
    CI
    README Format
    Tcl Format
    Man pages Test Framework
    Code of Conduct
    FAQs

    Your response must be in this exact JSON format:
    {
      "questions": [
        "",
        "",
        ""
      ]
    }
    The first character should be '{' and the last character should be '}'. Do not include any additional text or formatting.`;

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${process.env.GEMINI_API_KEY}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contents: [
              {
                parts: [
                  {
                    text: `${prompt}\n\nUser Question: ${latestQuestion}\n\nAssistant Answer: ${assistantAnswer}`,
                  },
                ],
              },
            ],
          }),
        }
      );

      const data = await response.json();
      const suggestedQuestionsText = data.candidates[0].content.parts[0].text;
      const trimmedText = suggestedQuestionsText.substring(
        suggestedQuestionsText.indexOf("{"),
        suggestedQuestionsText.lastIndexOf("}") + 1
      );
      const suggestedQuestions = JSON.parse(trimmedText);
      // Trim the response

      setQuestions(suggestedQuestions.questions);
    } catch (error) {
      console.error("Error fetching suggested questions:", error);
      setQuestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow transition-colors duration-200 ${
        isMobile ? "max-w-full" : "max-w-[90%]"
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
