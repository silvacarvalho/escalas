import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { Toaster } from "@/components/ui/sonner";

// Suppress ResizeObserver errors (known issue with Radix UI components)
const resizeObserverError = (e) => {
  if (
    e.message === 'ResizeObserver loop completed with undelivered notifications.' ||
    e.message === 'ResizeObserver loop limit exceeded'
  ) {
    const resizeObserverErrDiv = document.getElementById(
      'webpack-dev-server-client-overlay-div'
    );
    const resizeObserverErr = document.getElementById(
      'webpack-dev-server-client-overlay'
    );
    if (resizeObserverErr) {
      resizeObserverErr.setAttribute('style', 'display: none');
    }
    if (resizeObserverErrDiv) {
      resizeObserverErrDiv.setAttribute('style', 'display: none');
    }
  }
};

window.addEventListener('error', resizeObserverError);

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
    <Toaster position="top-right" />
  </React.StrictMode>,
);
