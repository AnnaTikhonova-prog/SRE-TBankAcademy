import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api, { TOKEN_KEY } from './api.js';

// Контекст авторизации: хранит текущего пользователя и операции
// login/register/logout. Токен лежит в localStorage и переживает
// перезагрузку страницы; при старте проверяем его через /auth/me.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    // JWT stateless: сервер сессий не хранит, выход — просто удалить токен.
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const { data } = await api.get('/auth/me');
    setUser(data);
    return data;
  }, []);

  const login = useCallback(
    async (email, password) => {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      return refreshUser();
    },
    [refreshUser],
  );

  const register = useCallback(
    async ({ fullName, email, password, role }) => {
      await api.post('/auth/register', {
        full_name: fullName,
        email,
        password,
        role,
      });
      // После успешной регистрации сразу входим.
      return login(email, password);
    },
    [login],
  );

  // При загрузке приложения восстанавливаем сессию по сохранённому токену.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    refreshUser()
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false));
  }, [refreshUser]);

  // Глобальный выход по событию от axios-перехватчика (истёкший токен).
  useEffect(() => {
    window.addEventListener('auth:logout', logout);
    return () => window.removeEventListener('auth:logout', logout);
  }, [logout]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
