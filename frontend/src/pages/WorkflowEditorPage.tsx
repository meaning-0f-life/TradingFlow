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
        }).catch((error) => {
          console.error('Failed to load workflow:', error);
          toast.error('Failed to load workflow');
          navigate('/');
        });
      }
    }
  }, [isEditing, id, currentWorkflow, setCurrentWorkflow, setNodes, setEdges, navigate, availableNodeTypes]);

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

  const deleteSelectedNode = useCallback(() => {
    if (!selectedNode) return;

    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
    setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
    setSelectedNode(null);
  }, [selectedNode, setNodes, setEdges]);

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
        await updateWorkflow(parseInt(id), { config: workflowConfig });
        toast.success('Workflow updated successfully');
      } else {
        const name = newWorkflowName.trim() || `Workflow ${new Date().toLocaleDateString()}`;
        const workflow = await createWorkflow({ name, config: workflowConfig });
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
  }, [user, isEditing, id, nodes, edges, createWorkflow, updateWorkflow, navigate, newWorkflowName]);

  const runWorkflow = useCallback(async () => {
    if (!id || isRunning) return;

    setIsRunning(true);
    try {
      const execution = await executionAPI.run(parseInt(id));
      if (execution) {
        toast.success('Workflow execution started');
        navigate(`/executions?workflow_id=${id}`);
      }
    } catch (error: any) {
      toast.error('Failed to start workflow execution');
    } finally {
      setIsRunning(false);
    }
  }, [id, isRunning, navigate]);

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
        nodeCount={nodes.length}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* React Flow Canvas */}
        <div className="flex-1 h-full">
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
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const nodeType = node.data.nodeType;
                const colors: Record<string, string> = {
                  llm: '#3b82f6',
                  data_fetcher: '#10b981',
                };
                return colors[nodeType] || '#6b7280';
              }}
            />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>

        {/* Configuration Panel */}
        {selectedNode && (
          <div className="w-80 bg-slate-800 border-l border-slate-700 overflow-y-auto">
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
    </div>
  );
}