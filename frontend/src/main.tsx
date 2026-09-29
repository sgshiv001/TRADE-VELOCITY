import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./professional.css";

document.documentElement.dataset.theme = localStorage.getItem("tradevelocity-theme") === "dark" ? "dark" : "light";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
