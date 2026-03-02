import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useWorkflowStore } from '@/store/workflowStore';
import { useAuthStore } from '@/store/authStore';
import LoadingSpinner from '@/components/LoadingSpinner';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const { workflows, isLoading, error, fetchWorkflows, deleteWorkflow } = useWorkflowStore();
  const { user } = useAuthStore();

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      await deleteWorkflow(id);
    }
  };

  if (isLoading && workflows.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Welcome back, {user?.username}!</p>
        </div>
        <Link
          to="/workflows/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          New Workflow
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
          {error}
        </div>
      )}

      {workflows.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center border border-slate-700">
          <h3 className="text-xl font-semibold text-white mb-4">No workflows yet</h3>
          <p className="text-slate-400 mb-6">
            Create your first workflow to start automating your trading and analysis.
          </p>
          <Link
            to="/workflows/new"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            Create Workflow
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-blue-500 transition-colors"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-white truncate flex-1">
                  {workflow.name}
                </h3>
                <span className="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded">
                  v{workflow.version}
                </span>
              </div>

              <p className="text-slate-400 text-sm mb-4 line-clamp-2">
                {workflow.description || 'No description'}
              </p>

              <div className="text-xs text-slate-500 mb-4">
                <p>Nodes: {workflow.config.nodes?.length || 0}</p>
                <p>Connections: {workflow.config.edges?.length || 0}</p>
                <p>Created: {new Date(workflow.created_at).toLocaleDateString()}</p>
              </div>

              <div className="flex gap-2">
                <Link
                  to={`/workflows/${workflow.id}`}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                >
                  <PencilIcon className="w-4 h-4" />
                  Edit
                </Link>
                <Link
                  to={`/executions?workflow_id=${workflow.id}`}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                >
                  <EyeIcon className="w-4 h-4" />
                  Runs
                </Link>
                <button
                  onClick={() => handleDelete(workflow.id)}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-red-900/50 hover:bg-red-900/70 text-red-200 rounded-lg transition-colors text-sm"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}