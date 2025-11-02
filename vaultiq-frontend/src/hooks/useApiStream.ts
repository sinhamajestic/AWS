import { useState, useCallback } from 'react';
import { ApiQueryRequest, ApiQueryResponse, ApiSource } from '../types/api';

interface UseApiStreamReturn {
  answer: string;
  sources: ApiSource[];
  isLoading: boolean;
  error: string | null;
  query: (request: ApiQueryRequest) => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook to handle streaming API responses from VaultIQ backend
 * Supports both streaming text and complete JSON responses
 */
export const useApiStream = (): UseApiStreamReturn => {
  const [answer, setAnswer] = useState<string>('');
  const [sources, setSources] = useState<ApiSource[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setAnswer('');
    setSources([]);
    setError(null);
  }, []);

  const query = useCallback(async (request: ApiQueryRequest) => {
    setIsLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);

    try {
      // Get API URL from environment or use default
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const endpoint = `${apiUrl}/api/query`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');

      // Check if response is JSON (non-streaming)
      if (contentType?.includes('application/json')) {
        const data: ApiQueryResponse = await response.json();
        setAnswer(data.answer);
        setSources(data.sources);
      } 
      // Handle streaming response (text/event-stream or chunked transfer)
      else if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              // Try to parse any remaining buffer as JSON for sources
              if (buffer.trim()) {
                try {
                  const finalData: ApiQueryResponse = JSON.parse(buffer);
                  if (finalData.sources) {
                    setSources(finalData.sources);
                  }
                } catch {
                  // Buffer wasn't valid JSON, that's okay
                }
              }
              break;
            }

            // Decode the chunk
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            // Try to parse as JSON to check if we got the complete response
            try {
              const jsonData: ApiQueryResponse = JSON.parse(buffer);
              // If we successfully parsed, we have the complete response
              setAnswer(jsonData.answer);
              if (jsonData.sources) {
                setSources(jsonData.sources);
              }
              buffer = ''; // Clear buffer after successful parse
            } catch {
              // Not complete JSON yet, treat as streaming text
              // Update answer progressively
              setAnswer(buffer);
            }
          }
        } catch (streamError) {
          console.error('Stream reading error:', streamError);
          throw new Error('Failed to read streaming response');
        }
      } else {
        throw new Error('No response body received');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('API query error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    answer,
    sources,
    isLoading,
    error,
    query,
    reset,
  };
};