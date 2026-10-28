import React from "react";
import ReactDOM from "react-dom/client";
import App from "./Workspace";
import AccessGate from "./AccessGate";
import "./styles.css";
import "./professional.css";
import "./cinematic.css";

try { document.documentElement.dataset.theme = localStorage.getItem("tradevelocity-theme") === "dark" ? "dark" : "light"; }
catch { document.documentElement.dataset.theme = "light"; }

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AccessGate><App /></AccessGate>
  </React.StrictMode>,
);
