import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import "./index.css";
import { client } from "./client/services.gen.ts";

import RootPage from "./routes/root.tsx";
import CctvPage from "./routes/cctv.tsx";

client.setConfig({
  baseUrl: "http://localhost:8000",
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootPage />,
    children: [
      {
        path: "cctv/",
        element: <CctvPage />,
      },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
