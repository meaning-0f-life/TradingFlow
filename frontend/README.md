# TradingFlow Frontend

React + TypeScript frontend for the TradingFlow visual workflow orchestration platform.

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: View and manage all your workflows
- **Visual Workflow Editor**: Drag-and-drop node-based editor using React Flow
- **Node Configuration**: Dynamic forms based on node type schemas
- **API Key Management**: Securely manage encrypted API credentials
- **Execution Monitoring**: Real-time workflow execution tracking with WebSocket updates
- **Modern UI**: Dark theme with Tailwind CSS

## Tech Stack

- **React 18** with TypeScript
- **React Flow** for visual node editing
- **Zustand** for state management
- **Tailwind CSS** for styling
- **Axios** for API communication
- **React Hot Toast** for notifications
- **Heroicons** for icons

## Getting Started

### Prerequisites

- Node.js 18+
- Backend running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   │   ├── CustomNode.tsx
│   │   ├── Layout.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── NodeConfigPanel.tsx
│   │   └── WorkflowToolbar.tsx
│   ├── pages/          # Page components
│   │   ├── ApiKeysPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ExecutionHistoryPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   └── WorkflowEditorPage.tsx
│   ├── services/       # API services
│   │   └── api.ts
│   ├── store/          # Zustand stores
│   │   ├── authStore.ts
│   │   ├── executionStore.ts
│   │   ├── nodeStore.ts
│   │   ├── websocketStore.ts
│   │   └── workflowStore.ts
│   ├── types/          # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx
│   ├── index.css
│   └── main.tsx
├── .gitignore
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── vite-env.d.ts
```

## API Integration

The frontend connects to the TradingFlow backend API:

- **Authentication**: `/api/auth/*`
- **Workflows**: `/api/workflows/*`
- **Execution**: `/api/execution/*`
- **Nodes**: `/api/nodes/*`
- **API Keys**: `/api/keys/*`
- **WebSocket**: `/ws`

## Configuration

Environment variables (create `.env` file):

```env
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Contributing

This frontend is designed to work with the TradingFlow backend. See the main README.md for backend development guidelines.