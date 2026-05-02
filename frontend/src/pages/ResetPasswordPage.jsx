import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { resetPassword } from "../api/auth";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token");

  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      await resetPassword({
        token,
        new_password: password,
      });

      setMessage("Password reset successful. Redirecting to login...");
      setTimeout(() => navigate("/login/customer"), 2000);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="landingPageShell">
      <div className="page landingPage">
        <h2>Reset Password</h2>

        <form onSubmit={handleSubmit} className="form">
          <input
            type="password"
            placeholder="Enter new password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Reset Password</button>
        </form>

        {message && <p>{message}</p>}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
