import { create } from 'zustand';
import type { Execution, ExecutionUpdateData } from '@/types';
import { executionAPI } from '@/services/api';
import { useWebSocketStore } from './websocketStore';

interface ExecutionState {
  executions: Execution[];
  currentExecution: Execution | null;
  isLoading: boolean;
  error: string | null;
  fetchExecutions: (workflow_id?: number) => Promise<void>;
  getExecution: (id: number) => Promise<void>;
  runWorkflow: (workflow_id: number, input_data?: Record<string, any>) => Promise<Execution | null>;
  clearError: () => void;
  setCurrentExecution: (execution: Execution | null) => void;
  updateExecutionFromWS: (executionId: number, updateData: ExecutionUpdateData) => void;
  subscribeToExecution: (executionId: number) => void;
  unsubscribeFromExecution: (executionId: number) => void;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  executions: [],
  currentExecution: null,
  isLoading: false,
  error: null,

  fetchExecutions: async (workflow_id?: number) => {
    set({ isLoading: true, error: null });
    try {
      const executions = await executionAPI.getAll(workflow_id);
      set({ executions, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch executions', isLoading: false });
    }
  },

  getExecution: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const execution = await executionAPI.getById(id);
      set({ currentExecution: execution, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch execution', isLoading: false });
    }
  },

  runWorkflow: async (workflow_id: number, input_data?: Record<string, any>) => {
    set({ isLoading: true, error: null });
    try {
      const execution = await executionAPI.run(workflow_id, input_data);
      set((state) => ({
        executions: [execution, ...state.executions],
        currentExecution: execution,
        isLoading: false,
      }));
      
      // Subscribe to WebSocket updates for this execution
      get().subscribeToExecution(execution.id);
      
      return execution;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to run workflow', isLoading: false });
      return null;
    }
  },

  setCurrentExecution: (execution: Execution | null) => {
    set({ currentExecution: execution });
  },

  clearError: () => set({ error: null }),

  subscribeToExecution: (executionId: number) => {
    const { subscribe } = useWebSocketStore.getState();
    subscribe(executionId);
  },

  unsubscribeFromExecution: (executionId: number) => {
    const { unsubscribe } = useWebSocketStore.getState();
    unsubscribe(executionId);
  },

  updateExecutionFromWS: (executionId: number, updateData: ExecutionUpdateData) => {
    set((state) => {
      const newExecutions = state.executions.map((exec) => {
        if (exec.id === executionId) {
          // Update execution based on the WebSocket update
          const updatedExec = { ...exec };
          
          // Update status based on event type
          if (updateData.status) {
            // In a real implementation, you'd update the status field
            // For now, we'll just store the latest update data
          }
          
          // You could also merge result_data, error_message, etc.
          return updatedExec;
        }
        return exec;
      });

      // Update currentExecution if it's the one being updated
      const newCurrentExecution = state.currentExecution?.id === executionId
        ? { ...state.currentExecution, ...updateData }
        : state.currentExecution;

      return {
        executions: newExecutions,
        currentExecution: newCurrentExecution,
      };
    });
  },
}));