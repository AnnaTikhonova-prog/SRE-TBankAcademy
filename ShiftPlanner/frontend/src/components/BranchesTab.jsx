import { useCallback, useEffect, useState } from 'react';
import api, { errorText } from '../api.js';

const EMPTY_FORM = { name: '', address: '' };

// Вкладка «Филиалы»: список, добавление, редактирование в строке, удаление.
export default function BranchesTab() {
  const [branches, setBranches] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const { data } = await api.get('/branches/');
    setBranches(data);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(errorText(err)));
  }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.post('/branches/', {
        name: form.name.trim(),
        address: form.address.trim() || null,
      });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleUpdate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.patch(`/branches/${editId}`, {
        name: editForm.name.trim(),
        address: editForm.address.trim() || null,
      });
      setEditId(null);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Удалить филиал? Его смены также будут удалены.')) return;
    setError('');
    try {
      await api.delete(`/branches/${id}`);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <section className="card">
      <h2>Филиалы</h2>

      <form onSubmit={handleCreate} className="form form-inline">
        <input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Название филиала"
          required
        />
        <input
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
          placeholder="Адрес (необязательно)"
        />
        <button className="btn btn-primary">Добавить</button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      <table className="table">
        <thead>
          <tr>
            <th>Название</th>
            <th>Адрес</th>
            <th className="col-actions">Действия</th>
          </tr>
        </thead>
        <tbody>
          {branches.map((branch) =>
            editId === branch.id ? (
              <tr key={branch.id}>
                <td colSpan={3}>
                  <form onSubmit={handleUpdate} className="form form-inline">
                    <input
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      required
                    />
                    <input
                      value={editForm.address}
                      onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                      placeholder="Адрес"
                    />
                    <button className="btn btn-primary btn-sm">Сохранить</button>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => setEditId(null)}
                    >
                      Отмена
                    </button>
                  </form>
                </td>
              </tr>
            ) : (
              <tr key={branch.id}>
                <td>{branch.name}</td>
                <td>{branch.address || '—'}</td>
                <td className="col-actions">
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      setEditId(branch.id);
                      setEditForm({ name: branch.name, address: branch.address || '' });
                    }}
                  >
                    Изменить
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(branch.id)}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ),
          )}
          {branches.length === 0 && (
            <tr>
              <td colSpan={3} className="text-muted">
                Филиалов пока нет — добавьте первый.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
