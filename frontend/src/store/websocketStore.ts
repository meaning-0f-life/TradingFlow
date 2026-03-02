import { create } from 'zustand';
import type { WSMessage, ExecutionUpdateData } from '@/types';

interface WebSocketState {
  isConnected: boolean;
  currentExecutionId: number | null;
  updates: Array<{ execution_id: number; data: ExecutionUpdateData; timestamp: Date }>;
  connect: (executionId: number) => void;
  disconnect: () => void;
  handleMessage: (message: WSMessage) => void;
  clearUpdates: () => void;
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  isConnected: false,
  currentExecutionId: null,
  updates: [],

  connect: (executionId: number) => {
    const wsUrl = `ws://localhost:8000/ws?client_id=execution_${executionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ isConnected: true, currentExecutionId: executionId });
      console.log('WebSocket connected');
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

    // Store WebSocket instance in state (not serializable, so we'll handle separately)
    (window as any).ws = ws;
  },

  disconnect: () => {
    const ws = (window as any).ws;
    if (ws) {
      ws.close();
      delete (window as any).ws;
    }
    set({ isConnected: false, currentExecutionId: null });
  },

  handleMessage: (message: WSMessage) => {
    if (message.type === 'execution_update' && message.execution_id) {
      set((state) => ({
        updates: [
          ...state.updates,
          {
            execution_id: message.execution_id!,
            data: message.data as ExecutionUpdateData,
            timestamp: new Date(),
          },
        ],
      }));
    }
  },

  clearUpdates: () => set({ updates: [] }),
}));