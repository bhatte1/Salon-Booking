import { createContext, useContext, useState } from "react";
import { logoutUser } from "../api/auth.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem("access_token"));
  const [loading] = useState(false);

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

export function useAuth() {
  return useContext(AuthContext);
}
