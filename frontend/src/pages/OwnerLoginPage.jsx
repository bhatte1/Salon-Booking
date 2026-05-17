import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginOwner } from "../api/auth";
import { useAuth } from "../context/AuthContext.jsx";

export default function OwnerLoginPage() {
  const [form, setForm] = useState({
    username_or_email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      const result = await loginOwner(form);
      login(result.access_token, result.user);
      setMessage(`Welcome owner ${result.user.username}`);
      navigate("/dashboard/owner");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="landingPageShell">
      <div className="page landingPage">
        <h2>Owner Login</h2>

        <form onSubmit={onSubmit} className="form">
          <input
            placeholder="Username or Email"
            value={form.username_or_email}
            onChange={(e) => setForm({ ...form, username_or_email: e.target.value })}
            required
          />
          <input
            placeholder="Password"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <button type="submit">Login</button>
        </form>

        {message && <p>{message}</p>}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
