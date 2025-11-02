import React, { useState, FormEvent } from 'react';

interface SearchBarProps {
  isLoading: boolean;
  onSubmit: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ isLoading, onSubmit }) => {
  const [query, setQuery] = useState<string>('');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Logo/Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-xl">V</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-800">
          VaultIQ
        </h1>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center gap-3 card p-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your IT knowledge base..."
            className="flex-1 px-4 py-3 text-gray-700 placeholder-gray-400 focus:outline-none bg-transparent"
            disabled={isLoading}
          />
          
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="btn-primary flex items-center justify-center gap-2 min-w-[120px]"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <span>Search</span>
                <svg 
                  className="w-5 h-5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M14 5l7 7m0 0l-7 7m7-7H3" 
                  />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* Helpful hints */}
        {!isLoading && query.length === 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-gray-500">Try asking:</span>
            {[
              'How do I deploy to production?',
              'What is our incident response process?',
              'Show me the latest API documentation'
            ].map((hint, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(hint)}
                className="text-sm px-3 py-1 bg-white border border-gray-200 rounded-full hover:border-primary-500 hover:text-primary-600 transition-colors"
              >
                {hint}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBar;