import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Checkout } from "./pages/Checkout";
import { Pay } from "./pages/Pay";
import { Cabinet } from "./pages/Cabinet";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ROUTES } from "./lib/routes";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.landing} element={<Landing />} />
        <Route path={ROUTES.login} element={<Login />} />
        <Route path="/checkout/:planId" element={<Checkout />} />
        <Route path="/pay/:invoiceId" element={<Pay />} />
        <Route path={ROUTES.cabinet} element={<ProtectedRoute><Cabinet /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to={ROUTES.landing} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
