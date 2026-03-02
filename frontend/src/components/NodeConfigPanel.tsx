import { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { NodeTypeInfo, UIParameter } from '@/types';

interface NodeConfigPanelProps {
  node: {
    id: string;
    type: string;
    position: { x: number; y: number };
    data: {
      label: string;
      nodeType: string;
      config: Record<string, any>;
    };
  };
  nodeTypeInfo: NodeTypeInfo | undefined;
  onUpdate: (config: Record<string, any>) => void;
  onDelete: () => void;
}

export default function NodeConfigPanel({
  node,
  nodeTypeInfo,
  onUpdate,
  onDelete,
}: NodeConfigPanelProps) {
  const [config, setConfig] = useState<Record<string, any>>(node.data.config || {});

  useEffect(() => {
    setConfig(node.data.config || {});
  }, [node.data.config]);

  const handleChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    onUpdate(newConfig);
  };

  const renderInput = (param: UIParameter) => {
    const value = config[param.name] ?? param.default;

    // Get options from either enum (legacy) or options (new format)
    const getOptions = () => {
      if (param.options && param.options.length > 0) {
        return param.options;
      }
      if (param.enum && param.enum.length > 0) {
        return param.enum.map(opt => ({ value: opt, label: opt }));
      }
      return [];
    };

    const options = getOptions();

    switch (param.type) {
      case 'string':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={param.description}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value ?? param.default ?? ''}
            onChange={(e) => handleChange(param.name, parseFloat(e.target.value) || 0)}
            min={param.minimum}
            max={param.maximum}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );

      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={value ?? param.default ?? false}
            onChange={(e) => handleChange(param.name, e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-blue-500"
          />
        );

      case 'select':
        return (
          <select
            value={value ?? param.default ?? ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case 'multi_select':
        const selectedValues = Array.isArray(value) ? value : [];
        const handleToggle = (optionValue: string) => {
          const newValues = selectedValues.includes(optionValue)
            ? selectedValues.filter(v => v !== optionValue)
            : [...selectedValues, optionValue];
          handleChange(param.name, newValues);
        };
        return (
          <div className="space-y-2">
            {options.map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(opt.value)}
                  onChange={() => handleToggle(opt.value)}
                  className="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-300">{opt.label}</span>
              </label>
            ))}
          </div>
        );

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );
    }
  };

  if (!nodeTypeInfo) {
    return (
      <div className="p-6">
        <div className="text-slate-400 text-sm">Node type information not available</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">{nodeTypeInfo.display_name}</h3>
          <p className="text-sm text-slate-400 mt-1">{nodeTypeInfo.description}</p>
        </div>
        <button
          onClick={onDelete}
          className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded-lg transition-colors"
          title="Delete node"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Parameters */}
      {nodeTypeInfo.ui_schema.parameters.length > 0 ? (
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Configuration</h4>
          {nodeTypeInfo.ui_schema.parameters.map((param) => (
            <div key={param.name}>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                {param.title}
                {param.description && (
                  <span className="text-xs text-slate-500 block font-normal mt-1">
                    {param.description}
                  </span>
                )}
              </label>
              {renderInput(param)}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-slate-400 text-sm mb-4">No configurable parameters</div>
      )}

      {/* Outputs */}
      {nodeTypeInfo.ui_schema.outputs.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-700">
          <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Outputs</h4>
          <div className="space-y-2">
            {nodeTypeInfo.ui_schema.outputs.map((output) => (
              <div key={output.name} className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-white">{output.name}</span>
                <span className="text-slate-500">({output.type})</span>
                {output.description && (
                  <span className="text-slate-400 text-xs"> - {output.description}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Node ID */}
      <div className="mt-6 pt-4 border-t border-slate-700">
        <div className="text-xs text-slate-500">
          Node ID: <span className="text-slate-400 font-mono">{node.id}</span>
        </div>
      </div>
    </div>
  );
}