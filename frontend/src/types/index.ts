// React Flow types are imported from reactflow library
// Node and Edge types are used directly from 'reactflow'

// User types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

// Workflow types
export interface Workflow {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  is_active: boolean;
  config: WorkflowConfig;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface WorkflowConfig {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    nodeType: string;
    config: Record<string, any>;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  config: WorkflowConfig;
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  config?: WorkflowConfig;
  is_active?: boolean;
}

// Execution types
export interface Execution {
  id: number;
  workflow_id: number;
  triggered_by: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: Record<string, any>;
  result_data: {
    node_results?: Record<string, any>;
    execution_order?: string[];
    errors?: Array<{ node_id: string; error: string }>;
  };
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface ExecutionCreate {
  workflow_id: number;
  input_data?: Record<string, any>;
}

// API Key types
export interface APIKey {
  id: number;
  name: string;
  service: string;
  is_active: boolean;
  created_at: string;
}

export interface APIKeyCreate {
  name: string;
  service: string;
  key: string;
}

// Auth types
export interface UserCreate {
  email: string;
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// Node types
export interface NodeTypeInfo {
  name: string;
  display_name: string;
  description: string;
  category: string;
  ui_schema: UISchema;
}

export interface UISchema {
  parameters: UIParameter[];
  outputs: UIOutput[];
}

export interface UIParameter {
  name: string;
  type: string;
  title: string;
  default?: any;
  description?: string;
  minimum?: number;
  maximum?: number;
  enum?: string[];
}

export interface UIOutput {
  name: string;
  type: string;
  description: string;
}

// WebSocket types
export interface WSMessage {
  type: 'execution_update' | 'pong' | 'error';
  execution_id?: number;
  data?: any;
}

export interface ExecutionUpdateData {
  node_id?: string;
  status?: string;
  message?: string;
  result?: any;
  error?: string;
}