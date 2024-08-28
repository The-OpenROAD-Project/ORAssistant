import useWindowSize from "../hooks/useWindowSize";

interface SourceListProps {
  sources: string[];
}

const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  return (
    <div
      className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow transition-colors duration-200 ${
        isMobile ? "max-w-full" : "max-w-[90%]"
      }`}
    >
      <h3 className="font-bold mb-2 text-gray-800 dark:text-white">Sources:</h3>
      <ul className="space-y-2">
        {sources.map((source, index) => (
          <li key={index} className="break-words">
            <a
              href={source}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
            >
              {source}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SourceList;
