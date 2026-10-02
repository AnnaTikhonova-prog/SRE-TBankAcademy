import { useCallback, useEffect, useState } from 'react';
import api, { errorText, shortTime, WEEKDAYS } from '../api.js';

const EMPTY_FORM = { weekday: '0', start_time: '', end_time: '' };

// Вкладка «Моя доступность»: сотрудник указывает, в какие дни и часы
// он может работать. Менеджер видит эти интервалы при назначении смен.
export default function AvailabilityTab() {
  const [blocks, setBlocks] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const { data } = await api.get('/availability/my');
    setBlocks(data);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(errorText(err)));
  }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.post('/availability/', {
        weekday: Number(form.weekday),
        start_time: form.start_time,
        end_time: form.end_time,
      });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleDelete(id) {
    setError('');
    try {
      await api.delete(`/availability/${id}`);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <section className="card card-narrow">
      <h2>Моя доступность</h2>
      <p className="text-muted">
        Укажите, когда вы можете работать. Это увидит менеджер при назначении смен.
      </p>

      <form onSubmit={handleCreate} className="form form-inline">
        <select value={form.weekday} onChange={(e) => setForm({ ...form, weekday: e.target.value })}>
          {WEEKDAYS.map((name, idx) => (
            <option key={idx} value={idx}>
              {name}
            </option>
          ))}
        </select>
        <input
          type="time"
          value={form.start_time}
          onChange={(e) => setForm({ ...form, start_time: e.target.value })}
          required
        />
        <span className="dash">—</span>
        <input
          type="time"
          value={form.end_time}
          onChange={(e) => setForm({ ...form, end_time: e.target.value })}
          required
        />
        <button className="btn btn-primary">Добавить</button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      <table className="table">
        <thead>
          <tr>
            <th>День недели</th>
            <th>Время</th>
            <th className="col-actions">Действия</th>
          </tr>
        </thead>
        <tbody>
          {blocks.map((block) => (
            <tr key={block.id}>
              <td>{WEEKDAYS[block.weekday]}</td>
              <td>
                {shortTime(block.start_time)}–{shortTime(block.end_time)}
              </td>
              <td className="col-actions">
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(block.id)}>
                  Удалить
                </button>
              </td>
            </tr>
          ))}
          {blocks.length === 0 && (
            <tr>
              <td colSpan={3} className="text-muted">
                Вы ещё не указали доступность.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
