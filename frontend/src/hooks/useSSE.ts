/**
 * React hook for Server-Sent Events (SSE) connection.
 */
import { useEffect, useRef } from 'react';
import { getSSEClient, SSEClient, type SSEEvent } from '@/lib/sse';
import { auth } from '@/lib/api';

export function useSSE(
  onEvent?: (event: SSEEvent) => void,
  eventTypes: string[] = ['*']
) {
  const clientRef = useRef<SSEClient | null>(null);

  useEffect(() => {
    const token = auth.getToken();
    if (!token) {
      return; // Not authenticated
    }

    const client = getSSEClient('/events', token);
    clientRef.current = client;

    // Register handlers for specified event types
    eventTypes.forEach((eventType) => {
      client.on(eventType, (event) => {
        if (onEvent) {
          onEvent(event);
        }
      });
    });

    // Connect
    client.connect();

    // Cleanup on unmount
    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, []); // Only run once on mount

  return clientRef.current;
}

