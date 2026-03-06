import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  Node,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Connection,
  NodeTypes,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '@/store/workflowStore';
import { useNodeStore } from '@/store/nodeStore';
import { useAuthStore } from '@/store/authStore';
import { workflowsAPI } from '@/services/api';
import type { WorkflowConfig, WorkflowNode, WorkflowEdge as WorkflowEdgeType } from '@/types';

import WorkflowToolbar from '@/components/WorkflowToolbar';
import NodeConfigPanel from '@/components/NodeConfigPanel';
import CustomNode from '@/components/CustomNode';
import LoadingSpinner from '@/components/LoadingSpinner';
import { toast } from 'react-hot-toast';
import { executionAPI } from '@/services/api';
import { Dialog } from '@headlessui/react';

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

export default function WorkflowEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = !!id;

  const { user } = useAuthStore();
  const { createWorkflow, updateWorkflow, currentWorkflow, setCurrentWorkflow } = useWorkflowStore();
  const { nodeTypes: availableNodeTypes, fetchNodeTypes, isLoading: nodesLoading } = useNodeStore();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowDescription, setNewWorkflowDescription] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [nodeToDelete, setNodeToDelete] = useState<Node | null>(null);

  // Load node types on mount
  useEffect(() => {
    fetchNodeTypes();
  }, [fetchNodeTypes]);

  // Load workflow if editing
  useEffect(() => {
    if (isEditing && id) {
      const workflowId = parseInt(id);
      // Try to get from store first
      if (currentWorkflow?.id === workflowId) {
        const config = currentWorkflow.config as WorkflowConfig;
        const backendNodes = config.nodes || [];
        const rfNodes: Node[] = backendNodes.map((node: any) => {
          const nodeTypeInfo = availableNodeTypes[node.type];
          let nodeConfig = node.data?.config || {};
          
          // Apply defaults from UI schema if config is missing values
          if (nodeTypeInfo?.ui_schema?.parameters) {
            const defaults: Record<string, any> = {};
            nodeTypeInfo.ui_schema.parameters.forEach(param => {
              if (param.default !== undefined && nodeConfig[param.name] === undefined) {
                defaults[param.name] = param.default;
              }
            });
            nodeConfig = { ...defaults, ...nodeConfig };
          }
          
          return {
            id: node.id,
            type: 'custom',
            position: node.position,
            data: {
              label: node.data?.label || node.type,
              nodeType: node.type,
              config: nodeConfig,
            },
          };
        });
        setNodes(rfNodes);
        setEdges(config.edges || []);
        setNewWorkflowName(currentWorkflow.name);
        setNewWorkflowDescription(currentWorkflow.description || '');
      } else {
        // Fetch from API
        workflowsAPI.getById(workflowId).then((workflow) => {
          setCurrentWorkflow(workflow);
          const config = workflow.config as WorkflowConfig;
          const backendNodes = config.nodes || [];
          const rfNodes: Node[] = backendNodes.map((node: any) => {
            const nodeTypeInfo = availableNodeTypes[node.type];
            let nodeConfig = node.data?.config || {};
            
            // Apply defaults from UI schema if config is missing values
            if (nodeTypeInfo?.ui_schema?.parameters) {
              const defaults: Record<string, any> = {};
              nodeTypeInfo.ui_schema.parameters.forEach(param => {
                if (param.default !== undefined && nodeConfig[param.name] === undefined) {
                  defaults[param.name] = param.default;
                }
              });
              nodeConfig = { ...defaults, ...nodeConfig };
            }
            
            return {
              id: node.id,
              type: 'custom',
              position: node.position,
              data: {
                label: node.data?.label || node.type,
                nodeType: node.type,
                config: nodeConfig,
              },
            };
          });
          setNodes(rfNodes);
          setEdges(config.edges || []);
          setNewWorkflowName(workflow.name);
          setNewWorkflowDescription(workflow.description || '');
        }).catch((error) => {
          console.error('Failed to load workflow:', error);
          toast.error('Failed to load workflow');
          navigate('/');
        });
      }
    }
  }, [isEditing, id, currentWorkflow, setCurrentWorkflow, setNodes, setEdges, navigate, availableNodeTypes]);

  // Keyboard shortcut for deleting nodes
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNode) {
        // Don't delete if user is typing in an input
        if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
          return;
        }
        event.preventDefault();
        handleDeleteNode(selectedNode);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode]);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({
        ...params,
        type: 'smoothstep',
        animated: false,
      }, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    // Simply deselect any selected node when clicking on the pane
    setSelectedNode(null);
  }, []);

  const addNode = useCallback((nodeType: string) => {
    const nodeInfo = availableNodeTypes[nodeType];
    if (!nodeInfo) return;

    const id = `${nodeType}_${Date.now()}`;
    
    // Initialize config with default values from UI schema
    const defaultConfig: Record<string, any> = {};
    if (nodeInfo.ui_schema?.parameters) {
      nodeInfo.ui_schema.parameters.forEach(param => {
        if (param.default !== undefined) {
          defaultConfig[param.name] = param.default;
        }
      });
    }

    const newNode: Node = {
      id,
      type: 'custom',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        label: nodeInfo.display_name,
        nodeType,
        config: defaultConfig,
      },
    };

    setNodes((nds) => nds.concat(newNode));
    setSelectedNode(newNode);
  }, [availableNodeTypes, setNodes]);

  const updateSelectedNode = useCallback((config: Record<string, any>) => {
    if (!selectedNode) return;

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              config,
            },
          };
        }
        return node;
      })
    );

    setSelectedNode((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        data: {
          ...prev.data,
          config,
        },
      };
    });
  }, [selectedNode, setNodes]);

  const handleDeleteNode = useCallback((node: Node) => {
    setNodeToDelete(node);
    setShowDeleteConfirm(true);
  }, []);

  const confirmDeleteNode = useCallback(() => {
    if (!nodeToDelete) return;

    setNodes((nds) => nds.filter((n) => n.id !== nodeToDelete.id));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeToDelete.id && edge.target !== nodeToDelete.id));
    
    // If the deleted node is currently selected, clear selection
    if (selectedNode?.id === nodeToDelete.id) {
      setSelectedNode(null);
    }
    
    toast.success('Node deleted successfully');
    setShowDeleteConfirm(false);
    setNodeToDelete(null);
  }, [nodeToDelete, setNodes, setEdges, selectedNode]);

  const cancelDeleteNode = useCallback(() => {
    setShowDeleteConfirm(false);
    setNodeToDelete(null);
  }, []);

  // Expose delete handler for NodeConfigPanel
  const deleteSelectedNode = useCallback(() => {
    if (selectedNode) {
      handleDeleteNode(selectedNode);
    }
  }, [selectedNode, handleDeleteNode]);

  const saveWorkflow = useCallback(async () => {
    if (!user) return;

    setIsSaving(true);
    try {
      const backendNodes: WorkflowNode[] = nodes.map((node) => ({
        id: node.id,
        type: node.data.nodeType,
        position: node.position,
        data: {
          label: node.data.label,
          nodeType: node.data.nodeType,
          config: node.data.config,
        },
      }));
      const workflowConfig: WorkflowConfig = {
        nodes: backendNodes,
        edges: edges as WorkflowEdgeType[],
      };

      if (isEditing && id) {
        await updateWorkflow(parseInt(id), {
          config: workflowConfig,
          name: newWorkflowName.trim() || undefined,
          description: newWorkflowDescription.trim() || undefined,
        });
        toast.success('Workflow updated successfully');
      } else {
        const name = newWorkflowName.trim() || `Workflow ${new Date().toLocaleDateString()}`;
        const description = newWorkflowDescription.trim() || undefined;
        const workflow = await createWorkflow({ name, description, config: workflowConfig });
        if (workflow) {
          toast.success('Workflow created successfully');
          navigate(`/workflows/${workflow.id}`);
        }
      }
    } catch (error: any) {
      toast.error(isEditing ? 'Failed to update workflow' : 'Failed to create workflow');
    } finally {
      setIsSaving(false);
    }
  }, [user, isEditing, id, nodes, edges, createWorkflow, updateWorkflow, navigate, newWorkflowName, newWorkflowDescription]);

  const runWorkflow = useCallback(async () => {
    if (!id || isRunning) return;

    setIsRunning(true);
    try {
      const execution = await executionAPI.run(parseInt(id));
      if (execution) {
        toast.success('Workflow execution started');
        // No automatic redirect - execution continues in background
        // User can manually navigate to Execution History to see updates
      }
    } catch (error: any) {
      toast.error('Failed to start workflow execution');
    } finally {
      setIsRunning(false);
    }
  }, [id, isRunning]);

  // Auto-save on changes (debounced in real app)
  useEffect(() => {
    if (isEditing && currentWorkflow) {
      // Could implement auto-save here
    }
  }, [nodes, edges, isEditing, currentWorkflow]);

  if (nodesLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <WorkflowToolbar
        onAddNode={addNode}
        nodeTypes={availableNodeTypes}
        onSave={saveWorkflow}
        onRun={runWorkflow}
        isSaving={isSaving}
        isRunning={isRunning}
        canRun={!!id && nodes.length > 0}
        isCreating={!isEditing}
        workflowName={newWorkflowName}
        onWorkflowNameChange={setNewWorkflowName}
        workflowDescription={newWorkflowDescription}
        onWorkflowDescriptionChange={setNewWorkflowDescription}
        nodeCount={nodes.length}
      />

      <div className="flex-1 flex min-h-0">
        {/* React Flow Canvas */}
        <div className="flex-1 min-h-0 min-w-0">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls className="bg-slate-800 border border-slate-700" />
            <MiniMap
              nodeColor={(node) => {
                const nodeType = node.data.nodeType;
                const colors: Record<string, string> = {
                  llm: '#3b82f6',
                  data_fetcher: '#10b981',
                };
                return colors[nodeType] || '#6b7280';
              }}
              className="bg-slate-800"
              maskColor="rgba(15, 23, 42, 0.8)"
            />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>

        {/* Configuration Panel */}
        {selectedNode && (
          <div className="w-80 min-w-0 bg-slate-800 border-l border-slate-700 overflow-auto h-full max-h-full">
            <NodeConfigPanel
              node={{
                id: selectedNode.id,
                type: selectedNode.type || 'custom',
                position: selectedNode.position,
                data: {
                  label: selectedNode.data.label,
                  nodeType: selectedNode.data.nodeType,
                  config: selectedNode.data.config,
                },
              }}
              nodeTypeInfo={availableNodeTypes[selectedNode.data.nodeType]}
              onUpdate={updateSelectedNode}
              onDelete={deleteSelectedNode}
            />
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onClose={cancelDeleteNode} className="relative z-50">
        <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-w-md w-full p-6">
            <Dialog.Title className="text-lg font-semibold text-white mb-2">
              Delete Node
            </Dialog.Title>
            <Dialog.Description className="text-slate-300 mb-6">
              Are you sure you want to delete the node "{nodeToDelete?.data.label}"?
              This action cannot be undone and will also remove all connections to this node.
            </Dialog.Description>
            <div className="flex justify-end gap-3">
              <button
                onClick={cancelDeleteNode}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteNode}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div>
  );
}