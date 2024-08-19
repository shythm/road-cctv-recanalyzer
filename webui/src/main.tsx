import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import "./index.css";
import { client } from "./client/services.gen.ts";

import RootPage from "./routes/root.tsx";
import RecordPage from "./routes/record.tsx";
import TrackPage from "./routes/track.tsx";

client.setConfig({
  baseUrl: "http://localhost:8000",
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootPage />,
    children: [
      { path: "/", element: <RecordPage /> },
      {
        path: "record/",
        element: <RecordPage />,
      },
      {
        path: "track/",
        element: <TrackPage />,
      },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
