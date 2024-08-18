import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import "./index.css";
import { client } from "./client/services.gen.ts";

import RootPage from "./routes/root.tsx";
import RecordPage from "./routes/record.tsx";

client.setConfig({
  baseUrl: "http://localhost:8000",
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootPage />,
    children: [
      {
        path: "record/",
        element: <RecordPage />,
      },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
