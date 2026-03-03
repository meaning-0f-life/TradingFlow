import { useState } from 'react';
import { PlusIcon, PlayIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { Transition } from '@headlessui/react';
import type { NodeTypeInfo } from '@/types';

interface WorkflowToolbarProps {
  onAddNode: (nodeType: string) => void;
  nodeTypes: Record<string, NodeTypeInfo>;
  onSave: () => void;
  onRun: () => void;
  isSaving: boolean;
  isRunning: boolean;
  canRun: boolean;
  isCreating?: boolean;
  workflowName?: string;
  onWorkflowNameChange?: (name: string) => void;
  workflowDescription?: string;
  onWorkflowDescriptionChange?: (description: string) => void;
  nodeCount?: number;
}

export default function WorkflowToolbar({
  onAddNode,
  nodeTypes,
  onSave,
  onRun,
  isSaving,
  isRunning,
  canRun,
  isCreating = false,
  workflowName = '',
  onWorkflowNameChange,
  workflowDescription = '',
  onWorkflowDescriptionChange,
  nodeCount = 0,
}: WorkflowToolbarProps) {
  const [showAddMenu, setShowAddMenu] = useState(false);

  const categories = Object.values(nodeTypes).reduce((acc, nodeType) => {
    if (!acc[nodeType.category]) {
      acc[nodeType.category] = [];
    }
    acc[nodeType.category].push(nodeType);
    return acc;
  }, {} as Record<string, NodeTypeInfo[]>);

  return (
    <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
      {/* Left side - Different for creating vs editing */}
      <div className="flex items-center gap-4">
        {isCreating ? (
          <div className="flex flex-col gap-2">
            <input
              type="text"
              value={workflowName}
              onChange={(e) => onWorkflowNameChange?.(e.target.value)}
              placeholder="Enter workflow name..."
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={workflowDescription}
              onChange={(e) => onWorkflowDescriptionChange?.(e.target.value)}
              placeholder="Enter workflow description (optional)..."
              rows={2}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={onSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors w-fit"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  Creating...
                </>
              ) : (
                'Create Workflow'
              )}
            </button>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-2">
              <input
                type="text"
                value={workflowName}
                onChange={(e) => onWorkflowNameChange?.(e.target.value)}
                placeholder="Workflow name..."
                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <textarea
                value={workflowDescription}
                onChange={(e) => onWorkflowDescriptionChange?.(e.target.value)}
                placeholder="Workflow description (optional)..."
                rows={2}
                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            <div className="relative">
              <button
                onClick={() => setShowAddMenu(!showAddMenu)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <PlusIcon className="w-5 h-5" />
                Add Node
              </button>

              <Transition
                show={showAddMenu}
                enter="transition ease-out duration-200"
                enterFrom="opacity-0 translate-y-1"
                enterTo="opacity-100 translate-y-0"
                leave="transition ease-in duration-150"
                leaveFrom="opacity-100 translate-y-0"
                leaveTo="opacity-0 translate-y-1"
              >
                <div className="absolute top-full left-0 mt-2 w-72 bg-slate-700 rounded-lg shadow-xl border border-slate-600 z-10 max-h-96 overflow-y-auto">
                  {Object.entries(categories).map(([category, types]) => (
                    <div key={category}>
                      <div className="px-4 py-2 text-xs font-semibold text-slate-400 uppercase bg-slate-800/50">
                        {category}
                      </div>
                      {types.map((type) => (
                        <button
                          key={type.name}
                          onClick={() => {
                            onAddNode(type.name);
                            setShowAddMenu(false);
                          }}
                          className="w-full px-4 py-3 text-left hover:bg-slate-600 transition-colors border-b border-slate-700 last:border-b-0"
                        >
                          <div className="text-white font-medium">{type.display_name}</div>
                          <div className="text-xs text-slate-400 mt-1">{type.description}</div>
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              </Transition>
            </div>
            <div className="text-slate-400 text-sm">
              {nodeCount} node{nodeCount !== 1 ? 's' : ''}
            </div>
          </>
        )}
      </div>

      {/* Right side - Action buttons (only show Run for existing workflows) */}
      <div className="flex items-center gap-3">
        {!isCreating && (
          <>
            <button
              onClick={onSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded-lg transition-colors"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  Saving...
                </>
              ) : (
                <>
                  <ArrowDownTrayIcon className="w-5 h-5" />
                  Save
                </>
              )}
            </button>

            <button
              onClick={onRun}
              disabled={!canRun || isRunning}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors"
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Running...
                </>
              ) : (
                <>
                  <PlayIcon className="w-5 h-5" />
                  Run
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}