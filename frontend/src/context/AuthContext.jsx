import { useEffect, useState } from "react";
import { getMe, logoutUser } from "../api/auth.js";

import { AuthContext } from "./auth-context.js";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem("access_token"));
  const [loading, setLoading] = useState(() => !!sessionStorage.getItem("access_token"));

  useEffect(() => {
    const savedToken = sessionStorage.getItem("access_token");
    if (!savedToken) return;
    let cancelled = false;

    async function restoreSession() {
      try {
        const authUser = await getMe(savedToken);
        if (!cancelled) setUser(authUser);
      } catch {
        if (!cancelled) {
          sessionStorage.removeItem("access_token");
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restoreSession();
    return () => { cancelled = true; };
  }, []);

  function login(_authToken, authUser) {
    if (_authToken) {
      sessionStorage.setItem("access_token", _authToken);
      setToken(_authToken);
    } else if (authUser) {
      setToken("session-active");
    }
    setUser(authUser);
  }

  async function logout() {
    try {
      await logoutUser();
    } catch (error) {
      console.error("Logout failed:", error.message);
    }
    sessionStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
