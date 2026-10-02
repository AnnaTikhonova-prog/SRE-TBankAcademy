import { useState } from 'react';
import { useAuth } from '../auth.jsx';
import { errorText } from '../api.js';

// Страница входа и регистрации (переключаются вкладками).
export default function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    role: 'employee',
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(form.email.trim(), form.password);
      } else {
        await register({
          fullName: form.fullName.trim(),
          email: form.email.trim(),
          password: form.password,
          role: form.role,
        });
      }
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-logo">ShiftPlanner</h1>
        <p className="auth-subtitle">Планирование рабочих смен для небольших команд</p>

        <div className="tabs tabs-center">
          <button
            className={`tab ${mode === 'login' ? 'tab-active' : ''}`}
            onClick={() => { setMode('login'); setError(''); }}
          >
            Вход
          </button>
          <button
            className={`tab ${mode === 'register' ? 'tab-active' : ''}`}
            onClick={() => { setMode('register'); setError(''); }}
          >
            Регистрация
          </button>
        </div>

        <form onSubmit={handleSubmit} className="form">
          {mode === 'register' && (
            <label className="field">
              <span>Имя и фамилия</span>
              <input
                value={form.fullName}
                onChange={update('fullName')}
                required
                placeholder="Иван Иванов"
              />
            </label>
          )}

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={update('email')}
              required
              placeholder="you@example.com"
            />
          </label>

          <label className="field">
            <span>Пароль{mode === 'register' && ' (минимум 8 символов)'}</span>
            <input
              type="password"
              value={form.password}
              onChange={update('password')}
              required
              minLength={mode === 'register' ? 8 : 1}
            />
          </label>

          {mode === 'register' && (
            <div className="field">
              <span>Роль</span>
              <div className="role-picker">
                <label className={`role-option ${form.role === 'employee' ? 'role-selected' : ''}`}>
                  <input
                    type="radio"
                    name="role"
                    value="employee"
                    checked={form.role === 'employee'}
                    onChange={update('role')}
                  />
                  Сотрудник
                </label>
                <label className={`role-option ${form.role === 'manager' ? 'role-selected' : ''}`}>
                  <input
                    type="radio"
                    name="role"
                    value="manager"
                    checked={form.role === 'manager'}
                    onChange={update('role')}
                  />
                  Менеджер
                </label>
              </div>
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          <button className="btn btn-primary btn-block" disabled={busy}>
            {busy ? 'Подождите…' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </form>

        <div className="demo-hint">
          <strong>Демо-аккаунты:</strong>
          <br />
          Менеджер — manager@example.com / manager123
          <br />
          Сотрудник — ivan@example.com / employee123
        </div>
      </div>
    </div>
  );
}
