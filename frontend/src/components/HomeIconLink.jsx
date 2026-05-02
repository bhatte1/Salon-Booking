import { Link, useLocation } from "react-router-dom";

export default function HomeIconLink() {
  const location = useLocation();

  if (location.pathname === "/") {
    return null;
  }

  return (
    <Link to="/" className="homeIconLink" aria-label="Go to home page">
      <svg
        viewBox="0 0 24 24"
        width="18"
        height="18"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M3 10.5L12 3l9 7.5" />
        <path d="M5 9.5V21h14V9.5" />
        <path d="M10 21v-6h4v6" />
      </svg>
      <span>Home</span>
    </Link>
  );
}
