import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="page">
      <h1>Salon Booking</h1>
      <p>Welcome to the salon portal.</p>

      <div className="actions">
        <Link to="/signup">
          <button>Customer Sign Up</button>
        </Link>

        <Link to="/login/customer">
          <button>Customer Login</button>
        </Link>

        <Link to="/login/owner">
          <button>Owner Login</button>
        </Link>
      </div>

      <div className="links">
        <Link to="/forgot-password">Forgot Password?</Link>
        <br />
        <Link to="/forgot-username">Forgot Username?</Link>
      </div>
    </div>
  );
}