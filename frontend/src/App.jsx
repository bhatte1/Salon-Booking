import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import SignupPage from "./pages/SignupPage";
import CustomerLoginPage from "./pages/CustomerLoginPage";
import OwnerLoginPage from "./pages/OwnerLoginPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ForgotUsernamePage from "./pages/ForgotUsernamePage";
import CustomerDashboardPage from "./pages/CustomerDashboardPage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import ProtectedRoute from "./components/ProtectedRoute";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import HomeIconLink from "./components/HomeIconLink";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <HomeIconLink />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login/customer" element={<CustomerLoginPage />} />
        <Route path="/login/owner" element={<OwnerLoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/forgot-username" element={<ForgotUsernamePage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        <Route
          path="/dashboard/customer"
          element={
            <ProtectedRoute allowedRole="customer">
              <CustomerDashboardPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard/owner"
          element={
            <ProtectedRoute allowedRole="owner">
              <OwnerDashboardPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
