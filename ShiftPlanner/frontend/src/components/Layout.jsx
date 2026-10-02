import { useAuth } from '../auth.jsx';

// Общий каркас страницы: шапка с названием, пользователем и кнопкой выхода,
// панель вкладок и контент.
export default function Layout({ title, tabs, activeTab, onTabChange, children }) {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <header className="header">
        <div className="header-brand">
          <span className="logo">ShiftPlanner</span>
          {title && <span className="header-title">{title}</span>}
        </div>
        <div className="header-user">
          <span className="user-name">{user?.full_name}</span>
          <span className={`badge badge-${user?.role}`}>
            {user?.role === 'manager' ? 'Менеджер' : 'Сотрудник'}
          </span>
          <button className="btn btn-ghost" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      {tabs && (
        <nav className="tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'tab-active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      )}

      <main className="content">{children}</main>
    </div>
  );
}
