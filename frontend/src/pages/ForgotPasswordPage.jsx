import { useState } from "react";
import { forgotPassword } from "../api/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [link, setLink] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    setLink("");

    try {
      const res = await forgotPassword({ email });
      setMessage(res.message);
      setLink(res.reset_link); // dev mode only
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2>Forgot Password</h2>

      <form onSubmit={handleSubmit} className="form">
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button type="submit">Send Reset Link</button>
      </form>

      {message && <p>{message}</p>}
      {link && (
        <p>
          Reset Link (dev): <a href={link}>{link}</a>
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}