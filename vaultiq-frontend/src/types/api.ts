/**
 * TypeScript interfaces for VaultIQ API communication
 */

// The JSON payload we send to the backend
export interface ApiQueryRequest {
  query: string;
  top_k?: number;
  source_filter?: string[];
}

// The shape of a single source object
export interface ApiSource {
  title: string;
  url: string;
  source_type: 'confluence' | 'slack' | 'jira' | 'github';
  relevance_score: number;
  snippet: string;
}

// The final JSON response from the API
export interface ApiQueryResponse {
  answer: string;
  sources: ApiSource[];
  query: string;
  timestamp: string;
}

// For streaming responses
export interface StreamChunk {
  type: 'token' | 'complete';
  content?: string;
  data?: ApiQueryResponse;
}

// Source metadata for display
export interface SourceMetadata {
  icon: string;
  color: string;
  label: string;
}

export const SOURCE_METADATA: Record<string, SourceMetadata> = {
  confluence: {
    icon: '📄',
    color: 'text-blue-600',
    label: 'Confluence'
  },
  slack: {
    icon: '💬',
    color: 'text-purple-600',
    label: 'Slack'
  },
  jira: {
    icon: '🎫',
    color: 'text-blue-500',
    label: 'Jira'
  },
  github: {
    icon: '🔧',
    color: 'text-gray-800',
    label: 'GitHub'
  }
};