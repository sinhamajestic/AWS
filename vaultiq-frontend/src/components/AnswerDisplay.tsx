import React from 'react';
import ReactMarkdown from 'react-markdown';

interface AnswerDisplayProps {
  answer: string;
  isStreaming: boolean;
}

const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ answer, isStreaming }) => {
  if (!answer) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mx-auto mt-8">
      <div className="card p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-200">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
            <svg 
              className="w-5 h-5 text-white" 
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
          <h2 className="text-xl font-semibold text-gray-800">
            AI-Generated Answer
          </h2>
          {isStreaming && (
            <div className="ml-auto flex items-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span>Generating...</span>
            </div>
          )}
        </div>

        {/* Answer Content with Markdown Support */}
        <div className="prose prose-slate max-w-none">
          <ReactMarkdown
            components={{
              // Custom styling for markdown elements
              p: ({ children }) => (
                <p className="text-gray-700 leading-relaxed mb-4">{children}</p>
              ),
              h1: ({ children }) => (
                <h1 className="text-2xl font-bold text-gray-900 mb-4 mt-6">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl font-bold text-gray-900 mb-3 mt-5">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-4">{children}</h3>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-inside space-y-2 mb-4 text-gray-700">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-700">{children}</ol>
              ),
              li: ({ children }) => (
                <li className="ml-4">{children}</li>
              ),
              code: ({ children, className }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="bg-gray-100 text-primary-700 px-1.5 py-0.5 rounded text-sm font-mono">
                    {children}
                  </code>
                ) : (
                  <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono my-4">
                    {children}
                  </code>
                );
              },
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-primary-500 pl-4 py-2 my-4 text-gray-600 italic">
                  {children}
                </blockquote>
              ),
              a: ({ children, href }) => (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-700 underline"
                >
                  {children}
                </a>
              ),
            }}
          >
            {answer}
          </ReactMarkdown>
          
          {/* Streaming cursor effect */}
          {isStreaming && (
            <span className="inline-block w-0.5 h-5 bg-gray-700 animate-pulse ml-0.5"></span>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnswerDisplay;