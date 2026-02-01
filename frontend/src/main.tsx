import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Import styles
import './styles/globals.css';
import './styles/animations.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
