import React from 'react';
import SearchBar from './components/SearchBar';
import AnswerDisplay from './components/AnswerDisplay';
import SourcesDisplay from './components/SourcesDisplay';
import { useApiStream } from './hooks/useApiStream';

const App: React.FC = () => {
  const { answer, sources, isLoading, error, query, reset } = useApiStream();

  const handleSearch = async (queryText: string) => {
    // Reset previous results before new search
    reset();
    
    // Execute the query
    await query({
      query: queryText,
      top_k: 5,
    });
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="container mx-auto">
        {/* Search Bar */}
        <SearchBar isLoading={isLoading} onSubmit={handleSearch} />

        {/* Error Display */}
        {error && (
          <div className="w-full max-w-4xl mx-auto mt-8">
            <div className="card p-4 border-l-4 border-red-500 bg-red-50">
              <div className="flex items-start gap-3">
                <svg 
                  className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
                <div className="flex-1">
                  <h3 className="font-semibold text-red-800 mb-1">
                    Error
                  </h3>
                  <p className="text-sm text-red-700">
                    {error}
                  </p>
                  <button
                    onClick={reset}
                    className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && !answer && (
          <div className="w-full max-w-4xl mx-auto mt-8">
            <div className="card p-8">
              <div className="flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg 
                      className="w-6 h-6 text-primary-600" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" 
                      />
                    </svg>
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-gray-700 font-medium mb-1">
                    Searching knowledge base...
                  </p>
                  <p className="text-sm text-gray-500">
                    Analyzing Confluence, Slack, Jira, and GitHub
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Answer Display */}
        <AnswerDisplay answer={answer} isStreaming={isLoading && answer.length > 0} />

        {/* Sources Display */}
        <SourcesDisplay sources={sources} />

        {/* Welcome State - Show when no query has been made */}
        {!answer && !isLoading && !error && (
          <div className="w-full max-w-4xl mx-auto mt-12">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full mb-6">
                <svg 
                  className="w-10 h-10 text-primary-600" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
                  />
                </svg>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-800 mb-3">
                Welcome to VaultIQ
              </h2>
              <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                Your AI-powered knowledge hub for IT management. 
                Ask questions and get instant answers from your Confluence docs, 
                Slack conversations, Jira tickets, and GitHub repositories.
              </p>

              {/* Feature Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                {[
                  { icon: '📄', label: 'Confluence', color: 'from-blue-500 to-blue-600' },
                  { icon: '💬', label: 'Slack', color: 'from-purple-500 to-purple-600' },
                  { icon: '🎫', label: 'Jira', color: 'from-blue-400 to-blue-500' },
                  { icon: '🔧', label: 'GitHub', color: 'from-gray-700 to-gray-800' },
                ].map((feature, idx) => (
                  <div key={idx} className="card p-4 text-center hover:shadow-lg transition-shadow">
                    <div className={`inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br ${feature.color} rounded-lg mb-2`}>
                      <span className="text-2xl">{feature.icon}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-700">{feature.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="w-full max-w-4xl mx-auto mt-16 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <p>
              Powered by AWS Bedrock (Claude 3 Haiku) and Amazon Titan Embeddings
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="hover:text-primary-600 transition-colors">
                Documentation
              </a>
              <a href="#" className="hover:text-primary-600 transition-colors">
                API Status
              </a>
              <a href="#" className="hover:text-primary-600 transition-colors">
                Support
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;