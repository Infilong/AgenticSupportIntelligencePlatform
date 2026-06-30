import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import "./styles.css";
import "./github-theme.css";
import "./sidebar-modern.css";
import "./workflow-rows.css";
import "./account-page.css";
import "./guardrails-page.css";
import "./scrollbars.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
