import { create } from 'zustand';
import type { Workflow, WorkflowCreate, WorkflowUpdate } from '@/types';
import { workflowsAPI, executionAPI } from '@/services/api';

interface WorkflowState {
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  isLoading: boolean;
  error: string | null;
  fetchWorkflows: () => Promise<void>;
  getWorkflow: (id: number) => Promise<void>;
  createWorkflow: (data: WorkflowCreate) => Promise<Workflow | null>;
  updateWorkflow: (id: number, data: WorkflowUpdate) => Promise<Workflow | null>;
  deleteWorkflow: (id: number) => Promise<boolean>;
  runWorkflow: (workflow_id: number, input_data?: Record<string, any>) => Promise<Workflow | null>;
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  clearError: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  currentWorkflow: null,
  isLoading: false,
  error: null,

  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    try {
      const workflows = await workflowsAPI.getAll();
      set({ workflows, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch workflows', isLoading: false });
    }
  },

  getWorkflow: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowsAPI.getById(id);
      set({ currentWorkflow: workflow, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch workflow', isLoading: false });
    }
  },

  createWorkflow: async (data: WorkflowCreate) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowsAPI.create(data);
      set((state) => ({
        workflows: [...state.workflows, workflow],
        isLoading: false,
      }));
      return workflow;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to create workflow', isLoading: false });
      return null;
    }
  },

  updateWorkflow: async (id: number, data: WorkflowUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowsAPI.update(id, data);
      set((state) => ({
        workflows: state.workflows.map((w) => (w.id === id ? workflow : w)),
        currentWorkflow: state.currentWorkflow?.id === id ? workflow : state.currentWorkflow,
        isLoading: false,
      }));
      return workflow;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to update workflow', isLoading: false });
      return null;
    }
  },

  deleteWorkflow: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      await workflowsAPI.delete(id);
      set((state) => ({
        workflows: state.workflows.filter((w) => w.id !== id),
        currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
        isLoading: false,
      }));
      return true;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to delete workflow', isLoading: false });
      return false;
    }
  },

  runWorkflow: async (workflow_id: number, input_data?: Record<string, any>) => {
    set({ isLoading: true, error: null });
    try {
      const execution = await executionAPI.run(workflow_id, input_data);
      set({ isLoading: false });
      return execution as unknown as Workflow;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to run workflow', isLoading: false });
      return null;
    }
  },

  setCurrentWorkflow: (workflow: Workflow | null) => {
    set({ currentWorkflow: workflow });
  },

  clearError: () => set({ error: null }),
}));