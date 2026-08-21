import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authService } from '../services/auth.service';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('money_analysis_user') || localStorage.getItem('costwise_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('money_analysis_token') || localStorage.getItem('costwise_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('money_analysis_token') || localStorage.getItem('costwise_token');
      if (storedToken) {
        try {
          const profile = await authService.getCurrentUser();
          setUser(profile);
          localStorage.setItem('money_analysis_user', JSON.stringify(profile));
        } catch {
          // Token invalid or expired
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('money_analysis_token', newToken);
    localStorage.setItem('money_analysis_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('money_analysis_token');
    localStorage.removeItem('money_analysis_user');
    localStorage.removeItem('costwise_token');
    localStorage.removeItem('costwise_user');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const profile = await authService.getCurrentUser();
      setUser(profile);
      localStorage.setItem('money_analysis_user', JSON.stringify(profile));
    } catch (e) {
      console.error('Failed to refresh user:', e);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
