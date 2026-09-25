/**
 * Resilient WebSocket Client for Electronic Warfare Simulation Gateway.
 * Manages auto-reconnect, status notifications, and typed event dispatching.
 */
import { EventMessage } from './types';

export type ConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED';
export type EventHandler = (data: any, timestamp: number) => void;

class EWWebSocketClient {
  private url: string;
  private ws: WebSocket | null = null;
  private status: ConnectionStatus = 'DISCONNECTED';
  private reconnectTimeout: any = null;
  private pingInterval: any = null;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private isExplicitlyClosed: boolean = false;

  constructor() {
    const rawWsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const wsBase = rawWsBase.replace(/\/+$/, '');
    this.url = `${wsBase}/ws`;
  }

  public getStatus(): ConnectionStatus {
    return this.status;
  }

  public onStatusChange(callback: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(callback);
    callback(this.status);
    return () => this.statusListeners.delete(callback);
  }

  private setStatus(status: ConnectionStatus) {
    if (this.status !== status) {
      this.status = status;
      this.statusListeners.forEach((listener) => listener(status));
    }
  }

  public connect(): void {
    if (typeof window === 'undefined') return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    this.setStatus('CONNECTING');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setStatus('CONNECTED');
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: EventMessage = JSON.parse(event.data);
          this.dispatchEvent(message.type, message.payload, message.timestamp);
        } catch (err) {
          console.error('[WebSocket] Error parsing incoming message:', err);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[WebSocket] Error:', err);
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.setStatus('DISCONNECTED');
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      this.setStatus('DISCONNECTED');
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('DISCONNECTED');
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      console.log('[WebSocket] Attempting to reconnect...');
      this.connect();
    }, 2500);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'PING' }));
      }
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  public subscribe(eventType: string, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    return () => {
      const set = this.handlers.get(eventType);
      if (set) {
        set.delete(handler);
      }
    };
  }

  private dispatchEvent(type: string, payload: any, timestamp: number): void {
    // Specific handlers
    const specificHandlers = this.handlers.get(type);
    if (specificHandlers) {
      specificHandlers.forEach((h) => h(payload, timestamp));
    }

    // Wildcard handlers
    const wildcardHandlers = this.handlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((h) => h({ type, payload, timestamp }, timestamp));
    }
  }

  public send(type: string, payload: any = {}): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }
}

export const wsClient = new EWWebSocketClient();
