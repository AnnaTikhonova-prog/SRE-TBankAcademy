import { useAuth } from './auth.jsx';
import AuthPage from './pages/AuthPage.jsx';
import ManagerPage from './pages/ManagerPage.jsx';
import EmployeePage from './pages/EmployeePage.jsx';

// Корневой компонент: выбирает экран по состоянию авторизации и роли.
export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="screen-loader">Загрузка…</div>;
  }
  if (!user) {
    return <AuthPage />;
  }
  return user.role === 'manager' ? <ManagerPage /> : <EmployeePage />;
}
