import { create } from 'zustand';
import type { NodeTypeInfo } from '@/types';
import { nodesAPI } from '@/services/api';

interface NodeStoreState {
  nodeTypes: Record<string, NodeTypeInfo>;
  isLoading: boolean;
  error: string | null;
  fetchNodeTypes: () => Promise<void>;
  clearError: () => void;
}

export const useNodeStore = create<NodeStoreState>((set) => ({
  nodeTypes: {},
  isLoading: false,
  error: null,

  fetchNodeTypes: async () => {
    set({ isLoading: true, error: null });
    try {
      const nodeTypes = await nodesAPI.getTypes();
      set({ nodeTypes, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to fetch node types', isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));