import { Navigate, Route, Routes } from "react-router-dom";

import { loadSession } from "./auth/session";
import { AppShell } from "./layouts/AppShell";
import { LoginPage } from "./pages/LoginPage";

function RequireAuth() {
  if (!loadSession()) {
    return <Navigate to="/login" replace />;
  }
  return <AppShell />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<RequireAuth />} />
    </Routes>
  );
}
