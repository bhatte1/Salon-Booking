import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="landingPageShell">
      <div className="page landingPage">
        <h1>Salon Booking</h1>
        <p>Welcome to the salon portal.</p>

        <div className="actions">
          {user && user.role === "customer" && (
            <Link to="/dashboard/customer">
              <button>Go to Customer Dashboard</button>
            </Link>
          )}

          {user && user.role === "owner" && (
            <Link to="/dashboard/owner">
              <button>Go to Owner Dashboard</button>
            </Link>
          )}

          {!user && (
            <>
              <Link to="/signup">
                <button>Customer Sign Up</button>
              </Link>

              <Link to="/login/customer">
                <button>Customer Login</button>
              </Link>

              <Link to="/login/owner">
                <button>Owner Login</button>
              </Link>
            </>
          )}
        </div>

        {!user && (
          <div className="links">
            <Link to="/forgot-password">Forgot Password?</Link>
            <br />
            <Link to="/forgot-username">Forgot Username?</Link>
          </div>
        )}
      </div>
    </div>
  );
}
