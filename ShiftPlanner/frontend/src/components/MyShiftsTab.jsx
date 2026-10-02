import { useCallback, useEffect, useState } from 'react';
import api, { errorText, formatDate, shortTime } from '../api.js';

// Вкладка «Мои смены»: сотрудник видит только свои смены.
export default function MyShiftsTab() {
  const [shifts, setShifts] = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    const { data } = await api.get('/shifts/', { params });
    setShifts(data);
  }, [dateFrom, dateTo]);

  useEffect(() => {
    load().catch((err) => setError(errorText(err)));
  }, [load]);

  return (
    <section className="card">
      <h2>Мои смены</h2>

      <div className="filters">
        <label className="field">
          <span>С</span>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label className="field">
          <span>По</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
        {(dateFrom || dateTo) && (
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setDateFrom('');
              setDateTo('');
            }}
          >
            Сбросить
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <table className="table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Время</th>
            <th>Должность</th>
            <th>Филиал</th>
          </tr>
        </thead>
        <tbody>
          {shifts.map((shift) => (
            <tr key={shift.id}>
              <td>{formatDate(shift.shift_date)}</td>
              <td>
                {shortTime(shift.start_time)}–{shortTime(shift.end_time)}
              </td>
              <td>{shift.position_name}</td>
              <td>{shift.branch_name}</td>
            </tr>
          ))}
          {shifts.length === 0 && (
            <tr>
              <td colSpan={4} className="text-muted">
                На выбранный период смен нет.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
