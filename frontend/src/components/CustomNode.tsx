import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface CustomNodeData {
  label: string;
  nodeType: string;
  config: Record<string, any>;
}

function CustomNode({ data, selected }: NodeProps<CustomNodeData>) {
  const getNodeIcon = (nodeType: string) => {
    switch (nodeType) {
      case 'llm':
        return '🤖';
      case 'data_fetcher':
        return '📊';
      default:
        return '📦';
    }
  };

  const getNodeColor = (nodeType: string) => {
    switch (nodeType) {
      case 'llm':
        return selected ? '#1d4ed8' : '#3b82f6';
      case 'data_fetcher':
        return selected ? '#047857' : '#10b981';
      default:
        return selected ? '#4b5563' : '#6b7280';
    }
  };

  return (
    <div
      className={`px-4 py-3 rounded-lg shadow-lg border-2 min-w-[180px] ${
        selected ? 'border-white' : 'border-slate-600'
      }`}
      style={{ backgroundColor: getNodeColor(data.nodeType) }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-white border-2 border-blue-500"
      />

      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{getNodeIcon(data.nodeType)}</span>
        <div className="text-white font-semibold text-sm truncate">{data.label}</div>
      </div>

      <div className="text-xs text-white/80">
        {Object.keys(data.config).length > 0 ? (
          <div className="space-y-1">
            {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
              <div key={key} className="truncate">
                <span className="text-white/60">{key}:</span> {String(value).slice(0, 20)}
              </div>
            ))}
            {Object.keys(data.config).length > 2 && (
              <div className="text-white/60">+{Object.keys(data.config).length - 2} more</div>
            )}
          </div>
        ) : (
          <div className="text-white/60 italic">Click to configure</div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-white border-2 border-blue-500"
      />
    </div>
  );
}

export default memo(CustomNode);