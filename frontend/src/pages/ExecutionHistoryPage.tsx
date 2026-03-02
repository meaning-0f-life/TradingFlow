import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useExecutionStore } from '@/store/executionStore';
import { useWebSocketStore } from '@/store/websocketStore';
import LoadingSpinner from '@/components/LoadingSpinner';
import { PlayIcon, CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

const STATUS_ICONS = {
  pending: ClockIcon,
  running: PlayIcon,
  completed: CheckCircleIcon,
  failed: XCircleIcon,
};

const STATUS_COLORS = {
  pending: 'text-yellow-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
};

export default function ExecutionHistoryPage() {
  const [searchParams] = useSearchParams();
  const workflowId = searchParams.get('workflow_id');

  const { executions, isLoading, error, fetchExecutions } = useExecutionStore();
  const { connect, disconnect, updates, isConnected } = useWebSocketStore();

  useEffect(() => {
    fetchExecutions(workflowId ? parseInt(workflowId) : undefined);
  }, [fetchExecutions, workflowId]);

  // Connect to WebSocket for latest execution
  useEffect(() => {
    if (executions.length > 0 && executions[0].status === 'running') {
      connect(executions[0].id);
    }
    return () => disconnect();
  }, [executions, connect, disconnect]);

  const getLatestUpdate = (executionId: number) => {
    return updates.find((u) => u.execution_id === executionId);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Execution History</h1>
        <p className="text-slate-400 mt-1">Monitor workflow executions in real-time</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
          {error}
        </div>
      )}

      {isLoading && executions.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : executions.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center border border-slate-700">
          <h3 className="text-xl font-semibold text-white mb-4">No executions yet</h3>
          <p className="text-slate-400">
            Run a workflow to see execution results here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {executions.map((execution) => {
            const StatusIcon = STATUS_ICONS[execution.status];
            const statusColor = STATUS_COLORS[execution.status];
            const latestUpdate = getLatestUpdate(execution.id);

            return (
              <div
                key={execution.id}
                className="bg-slate-800 rounded-xl p-6 border border-slate-700"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <StatusIcon className={`w-6 h-6 ${statusColor}`} />
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        Workflow #{execution.workflow_id}
                      </h3>
                      <p className="text-sm text-slate-400">
                        Started: {formatDate(execution.started_at)}
                        {execution.completed_at &&
                          ` • Completed: ${formatDate(execution.completed_at)}`}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${statusColor} bg-slate-700/50`}
                  >
                    {execution.status}
                  </span>
                </div>

                {execution.error_message && (
                  <div className="mb-4 p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-200 text-sm">
                    <strong>Error:</strong> {execution.error_message}
                  </div>
                )}

                {latestUpdate && latestUpdate.data?.message && (
                  <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700/50 rounded-lg text-blue-200 text-sm">
                    {latestUpdate.data.message}
                  </div>
                )}

                {execution.result_data?.node_results && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-slate-300 mb-2">Node Results:</h4>
                    <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
                      <pre className="text-xs text-slate-300">
                        {JSON.stringify(execution.result_data.node_results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {execution.result_data?.errors && execution.result_data.errors.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-red-400 mb-2">Errors:</h4>
                    <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
                      {execution.result_data.errors.map((err: any, idx: number) => (
                        <div key={idx} className="text-sm text-red-200 mb-1">
                          <strong>{err.node_id}:</strong> {err.error}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {isConnected && execution.status === 'running' && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-blue-400">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    Live updates connected
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}