import { create } from 'zustand';
import type { Execution } from '@/types';
import { executionAPI } from '@/services/api';

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
}

export const useExecutionStore = create<ExecutionState>((set) => ({
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
}));