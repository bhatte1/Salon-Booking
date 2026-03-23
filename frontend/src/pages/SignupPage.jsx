import { useState } from "react";
import { signupCustomer } from "../api/auth";

export default function SignupPage() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    username: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      const result = await signupCustomer(form);
      setMessage(`Signup successful for ${result.username}`);
      setForm({
        full_name: "",
        email: "",
        username: "",
        password: "",
      });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2>Customer Sign Up Page</h2>

      <form onSubmit={onSubmit} className="form">
        <input
          placeholder="Full Name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          placeholder="Username"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <button type="submit">Create Account</button>
      </form>

      {message && <p>{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}