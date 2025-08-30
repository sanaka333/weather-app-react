// Import the React Library (needed for JSX and building components)
import React from 'react';

// Import createRoot from react-dom/client
import { createRoot } from "react-dom/client";

// Import the CSS file so the app has global styles
import './index.css';

// Import the main App component (the root component of the app)
import App from './App';

// Import React Query client + provider
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a QueryClient instance
const queryClient = new QueryClient();

// Create a root container for React inside the <div id="root"> in index.html
const root = createRoot(document.getElementById('root'));

// Render the App component inside the root container
// React.StrictMode is a wrapper that checks for potential problems in development
// Wrap with QueryClientProvider so React Query works everywhere
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
    <App />
    </QueryClientProvider>
  </React.StrictMode>
);


