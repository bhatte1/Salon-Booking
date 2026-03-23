import { createContext, useContext, useEffect, useState } from "react";
import { getMe } from "../api/auth.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      const savedToken = localStorage.getItem("access_token");

      if (!savedToken) {
        setLoading(false);
        return;
      }

      try {
        const me = await getMe(savedToken);
        setUser(me);
        setToken(savedToken);
      } catch (error) {
        console.error("Session restore failed:", error.message);
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    }

    restoreSession();
  }, []);

  function login(authToken, authUser) {
    localStorage.setItem("access_token", authToken);
    localStorage.setItem("current_user", JSON.stringify(authUser));
    setToken(authToken);
    setUser(authUser);
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("current_user");
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