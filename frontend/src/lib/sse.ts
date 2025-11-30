/**
 * Server-Sent Events (SSE) client for real-time updates.
 */
export interface SSEEvent {
  type: string;
  data: unknown;
  timestamp?: string;
}

type EventHandler = (event: SSEEvent) => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private handlers: Map<string, EventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor(private url: string, private token: string | null) {}

  connect(): void {
    if (this.isConnecting || this.eventSource) {
      return;
    }

    this.isConnecting = true;
    const fullUrl = `${this.url}/stream${this.token ? `?token=${this.token}` : ''}`;
    
    this.eventSource = new EventSource(fullUrl, {
      withCredentials: true,
    });

    this.eventSource.onopen = () => {
      console.log('SSE connected');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
    };

    this.eventSource.onmessage = (event) => {
      try {
        const sseEvent: SSEEvent = JSON.parse(event.data);
        this.handleEvent(sseEvent.type, sseEvent);
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      this.isConnecting = false;
      
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        this.reconnect();
      }
    };
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.disconnect();
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Reconnecting SSE (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, delay);
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private handleEvent(eventType: string, event: SSEEvent): void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        console.error(`Error in SSE handler for ${eventType}:`, error);
      }
    });

    // Also call 'all' handlers
    const allHandlers = this.handlers.get('*') || [];
    allHandlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in SSE * handler:', error);
      }
    });
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.isConnecting = false;
  }
}

// Create singleton instance
let sseClient: SSEClient | null = null;

export function getSSEClient(baseUrl: string = '/events', token: string | null = null): SSEClient {
  if (!sseClient || sseClient !== sseClient) {
    sseClient = new SSEClient(baseUrl, token);
  }
  return sseClient;
}

