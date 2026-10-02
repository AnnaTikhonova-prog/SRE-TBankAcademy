import { useState } from 'react';
import api, { errorText } from '../api.js';
import { useAuth } from '../auth.jsx';

// Вкладка «Компания»: создание компании, просмотр кода приглашения,
// редактирование названия и адреса.
export default function CompanyTab() {
  const { user, refreshUser } = useAuth();
  const company = user?.company;

  const [createForm, setCreateForm] = useState({ name: '', address: '' });
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', address: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await api.post('/companies/', {
        name: createForm.name.trim(),
        address: createForm.address.trim() || null,
      });
      await refreshUser();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await api.patch('/companies/my', {
        name: editForm.name.trim(),
        address: editForm.address.trim() || null,
      });
      await refreshUser();
      setEditMode(false);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  // Компании ещё нет — предлагаем создать.
  if (!company) {
    return (
      <section className="card card-narrow">
        <h2>Создание компании</h2>
        <p className="text-muted">
          После создания вы получите код приглашения — по нему сотрудники
          смогут присоединиться к вашей компании.
        </p>
        <form onSubmit={handleCreate} className="form">
          <label className="field">
            <span>Название компании</span>
            <input
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              required
              placeholder="Кофейня «Уютная»"
            />
          </label>
          <label className="field">
            <span>Адрес (необязательно)</span>
            <input
              value={createForm.address}
              onChange={(e) => setCreateForm({ ...createForm, address: e.target.value })}
              placeholder="г. Москва, ул. Примерная, 1"
            />
          </label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary" disabled={busy}>
            {busy ? 'Создание…' : 'Создать компанию'}
          </button>
        </form>
      </section>
    );
  }

  return (
    <section className="card card-narrow">
      <h2>{company.name}</h2>

      <div className="invite-box">
        <span className="invite-label">Код приглашения для сотрудников:</span>
        <code className="invite-code">{company.invite_code}</code>
      </div>

      {!editMode ? (
        <div className="form">
          <p>
            <strong>Адрес:</strong> {company.address || '—'}
          </p>
          <button
            className="btn"
            onClick={() => {
              setEditForm({ name: company.name, address: company.address || '' });
              setEditMode(true);
            }}
          >
            Редактировать
          </button>
        </div>
      ) : (
        <form onSubmit={handleSave} className="form">
          <label className="field">
            <span>Название компании</span>
            <input
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              required
            />
          </label>
          <label className="field">
            <span>Адрес</span>
            <input
              value={editForm.address}
              onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
            />
          </label>
          {error && <div className="alert alert-error">{error}</div>}
          <div className="btn-row">
            <button className="btn btn-primary" disabled={busy}>
              Сохранить
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setEditMode(false)}>
              Отмена
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
