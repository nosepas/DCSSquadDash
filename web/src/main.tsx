import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { App } from './App';
import { AuthProvider } from './features/auth/AuthContext';
import { ServerProvider } from './features/servers/ServerContext';
import './i18n';
import './styles/index.css';

const root = document.getElementById('root');
if (!root) throw new Error('#root not found');

// A data router (instead of <BrowserRouter>) is required for useBlocker, used to protect unsaved admin edits.
const router = createBrowserRouter(
  [
    {
      path: '*',
      element: (
        <AuthProvider>
          <ServerProvider>
            <App />
          </ServerProvider>
        </AuthProvider>
      ),
    },
  ],
  { future: { v7_relativeSplatPath: true } },
);

createRoot(root).render(
  <StrictMode>
    <RouterProvider router={router} future={{ v7_startTransition: true }} />
  </StrictMode>,
);
