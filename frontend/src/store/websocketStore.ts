import { create } from 'zustand';
import type { WSMessage, ExecutionUpdateData } from '@/types';

interface ExecutionUpdate {
  execution_id: number;
  data: ExecutionUpdateData;
  timestamp: Date;
}

interface WebSocketState {
  isConnected: boolean;
  subscribedExecutions: number[];
  updates: Record<number, ExecutionUpdate[]>;
  connect: () => void;
  disconnect: () => void;
  subscribe: (executionId: number) => void;
  unsubscribe: (executionId: number) => void;
  handleMessage: (message: WSMessage) => void;
  getUpdatesForExecution: (executionId: number) => ExecutionUpdate[];
  clearUpdatesForExecution: (executionId: number) => void;
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  isConnected: false,
  subscribedExecutions: [],
  updates: {},

  connect: () => {
    // If already connected, don't create another connection
    if ((window as any).ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ isConnected: true });
      console.log('WebSocket connected globally');
      
      // Subscribe to all currently tracked executions
      const { subscribedExecutions } = get();
      subscribedExecutions.forEach((executionId: number) => {
        ws.send(JSON.stringify({
          type: 'subscribe',
          execution_id: executionId
        }));
      });
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        get().handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      set({ isConnected: false });
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      set({ isConnected: false });
    };

    // Store WebSocket instance
    (window as any).ws = ws;
  },

  disconnect: () => {
    const ws = (window as any).ws;
    if (ws) {
      ws.close();
      delete (window as any).ws;
    }
    set({ isConnected: false, subscribedExecutions: [] });
  },

  subscribe: (executionId: number) => {
    const { subscribedExecutions, isConnected } = get();
    
    if (subscribedExecutions.includes(executionId)) {
      console.log(`Already subscribed to execution ${executionId}`);
      return;
    }

    const newSubscribed = [...subscribedExecutions, executionId];
    set({ subscribedExecutions: newSubscribed });

    // Send subscription message if WebSocket is connected
    const ws = (window as any).ws;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        execution_id: executionId
      }));
      console.log(`Subscribed to execution ${executionId}`);
    }
  },

  unsubscribe: (executionId: number) => {
    const { subscribedExecutions } = get();
    
    if (!subscribedExecutions.includes(executionId)) {
      return;
    }

    const newSubscribed = subscribedExecutions.filter((id: number) => id !== executionId);
    set({ subscribedExecutions: newSubscribed });

    // Send unsubscribe message if WebSocket is connected
    const ws = (window as any).ws;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'unsubscribe',
        execution_id: executionId
      }));
      console.log(`Unsubscribed from execution ${executionId}`);
    }
  },

  handleMessage: (message: WSMessage) => {
    if (message.type === 'execution_update' && message.execution_id) {
      const executionId = message.execution_id;
      const update: ExecutionUpdate = {
        execution_id: executionId,
        data: message.data as ExecutionUpdateData,
        timestamp: new Date(),
      };

      set((state) => {
        const executionUpdates = state.updates[executionId] || [];
        return {
          updates: {
            ...state.updates,
            [executionId]: [...executionUpdates, update],
          },
        };
      });
    }
  },

  getUpdatesForExecution: (executionId: number) => {
    const { updates } = get();
    return updates[executionId] || [];
  },

  clearUpdatesForExecution: (executionId: number) => {
    set((state) => {
      const newUpdates = { ...state.updates };
      delete newUpdates[executionId];
      return { updates: newUpdates };
    });
  },
}));
