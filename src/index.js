// Import the React Library (needed for JSX and building components)
import React from 'react';

// Import ReactDOM from 'react-dom/client' (used to render React components into the browser DOM)
import ReactDOM from 'react-dom/client';

// Import the CSS file so the app has global styles
import './index.css';

// Import the main App component (the root component of the app)
import App from './App';

// Create a root container for React inside the <div id="root"> in index.html
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render the App component inside the root container
// React.StrictMode is a wrapper that checks for potential problems in development
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);


