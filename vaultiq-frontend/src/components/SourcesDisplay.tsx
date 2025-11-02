import React from 'react';
import { ApiSource, SOURCE_METADATA } from '../types/api';

interface SourcesDisplayProps {
  sources: ApiSource[];
}

const SourcesDisplay: React.FC<SourcesDisplayProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mx-auto mt-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <svg 
          className="w-6 h-6 text-gray-600" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
          />
        </svg>
        <h2 className="text-xl font-semibold text-gray-800">
          Sources ({sources.length})
        </h2>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sources.map((source, index) => {
          const metadata = SOURCE_METADATA[source.source_type] || {
            icon: '📄',
            color: 'text-gray-600',
            label: source.source_type
          };

          return (
            <a
              key={index}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="card p-4 hover:shadow-xl transition-shadow duration-200 group cursor-pointer"
            >
              {/* Source Type Badge */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">{metadata.icon}</span>
                <span className={`text-sm font-medium ${metadata.color}`}>
                  {metadata.label}
                </span>
                <div className="ml-auto">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <span className="font-medium">
                      {(source.relevance_score * 100).toFixed(0)}%
                    </span>
                    <span>match</span>
                  </div>
                </div>
              </div>

              {/* Title */}
              <h3 className="font-semibold text-gray-800 mb-2 group-hover:text-primary-600 transition-colors line-clamp-2">
                {source.title}
              </h3>

              {/* Snippet */}
              <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                {source.snippet}
              </p>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <svg 
                    className="w-3 h-3" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" 
                    />
                  </svg>
                  <span>View Source</span>
                </div>
                <svg 
                  className="w-4 h-4 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9 5l7 7-7 7" 
                  />
                </svg>
              </div>
            </a>
          );
        })}
      </div>

      {/* Show more hint if there are many sources */}
      {sources.length > 6 && (
        <div className="mt-4 text-center">
          <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            Show all {sources.length} sources
          </button>
        </div>
      )}
    </div>
  );
};

export default SourcesDisplay;