import useWindowSize from '../hooks/useWindowSize';

interface ContextSource {
  source?: string;
  context?: string;
}

interface SourceListProps {
  sources: ContextSource[];
}

const extractFirstUrl = (text: string): string => {
  const urlPattern = /(https?:\/\/[^\s)]+)(?=[)\s]|$)/i;
  const match = text.match(urlPattern);
  return match ? match[0] : '';
};

const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  const { width } = useWindowSize();
  const isMobile = width !== undefined && width <= 768;

  const derivedSources = sources
    .map((sourceItem) => {
      const context = sourceItem.context?.trim();
      const rawSource = sourceItem.source?.trim();
      return rawSource || (context ? extractFirstUrl(context) : '');
    })
    .filter((derivedSource): derivedSource is string => Boolean(derivedSource));

  if (!derivedSources.length) {
    return null;
  }

  return (
    <div
      className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow transition-colors duration-200 ${
        isMobile ? 'max-w-full' : 'max-w-[90%]'
      }`}
    >
      <h3 className="font-bold mb-2 text-gray-800 dark:text-white">Sources</h3>
      <ul className="space-y-2">
        {derivedSources.map((derivedSource, index) => (
          <li key={`${derivedSource}-${index}`} className="break-words">
            <a
              href={derivedSource}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
            >
              {derivedSource}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SourceList;
