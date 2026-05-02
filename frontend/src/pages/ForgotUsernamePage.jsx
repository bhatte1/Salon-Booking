import { useState } from "react";
import { forgotUsername } from "../api/auth";

export default function ForgotUsernamePage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      const res = await forgotUsername({ email });
      setMessage(res.message);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="landingPageShell">
      <div className="page landingPage">
        <h2>Forgot Username</h2>

        <form onSubmit={handleSubmit} className="form">
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit">Find Username</button>
        </form>

        {message && <p>{message}</p>}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
