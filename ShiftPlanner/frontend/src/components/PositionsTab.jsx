import { useCallback, useEffect, useState } from 'react';
import api, { errorText } from '../api.js';

// Вкладка «Должности»: список, добавление, переименование, удаление.
export default function PositionsTab() {
  const [positions, setPositions] = useState([]);
  const [name, setName] = useState('');
  const [editId, setEditId] = useState(null);
  const [editName, setEditName] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const { data } = await api.get('/positions/');
    setPositions(data);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(errorText(err)));
  }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.post('/positions/', { name: name.trim() });
      setName('');
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleUpdate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.patch(`/positions/${editId}`, { name: editName.trim() });
      setEditId(null);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Удалить должность?')) return;
    setError('');
    try {
      await api.delete(`/positions/${id}`);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <section className="card card-narrow">
      <h2>Должности</h2>

      <form onSubmit={handleCreate} className="form form-inline">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Например: Бариста"
          required
        />
        <button className="btn btn-primary">Добавить</button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      <table className="table">
        <thead>
          <tr>
            <th>Название</th>
            <th className="col-actions">Действия</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) =>
            editId === position.id ? (
              <tr key={position.id}>
                <td colSpan={2}>
                  <form onSubmit={handleUpdate} className="form form-inline">
                    <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
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
              <tr key={position.id}>
                <td>{position.name}</td>
                <td className="col-actions">
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      setEditId(position.id);
                      setEditName(position.name);
                    }}
                  >
                    Изменить
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(position.id)}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ),
          )}
          {positions.length === 0 && (
            <tr>
              <td colSpan={2} className="text-muted">
                Должностей пока нет — добавьте первую.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
