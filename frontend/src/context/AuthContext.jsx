import { createContext, useContext, useEffect, useState } from "react";
import { getMe, logoutUser } from "../api/auth.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem("access_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      const savedToken = sessionStorage.getItem("access_token");
      try {
        const me = await getMe(savedToken || undefined);
        setUser(me);
        setToken(savedToken || "cookie-session");
      } catch (error) {
        console.error("Session restore failed:", error.message);
        sessionStorage.removeItem("access_token");
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    }

    restoreSession();
  }, []);

  function login(_authToken, authUser) {
    if (_authToken) {
      sessionStorage.setItem("access_token", _authToken);
      setToken(_authToken);
    } else {
      setToken("cookie-session");
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

export function useAuth() {
  return useContext(AuthContext);
}
