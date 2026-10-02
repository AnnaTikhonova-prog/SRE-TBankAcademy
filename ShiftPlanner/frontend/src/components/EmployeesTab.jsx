import { Fragment, useCallback, useEffect, useState } from 'react';
import api, { errorText, shortTime, WEEKDAYS } from '../api.js';

// Вкладка «Сотрудники»: список сотрудников компании, назначение филиала
// и должности, деактивация/удаление, просмотр недельной доступности.
export default function EmployeesTab() {
  const [employees, setEmployees] = useState([]);
  const [branches, setBranches] = useState([]);
  const [positions, setPositions] = useState([]);
  // availabilityById[id] — загруженная доступность сотрудника (или null).
  const [availabilityById, setAvailabilityById] = useState({});
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [emp, br, pos] = await Promise.all([
      api.get('/employees/'),
      api.get('/branches/'),
      api.get('/positions/'),
    ]);
    setEmployees(emp.data);
    setBranches(br.data);
    setPositions(pos.data);
  }, []);

  useEffect(() => {
    load().catch((err) => setError(errorText(err)));
  }, [load]);

  // Обновление одного поля сотрудника (филиал/должность/активность).
  async function updateEmployee(id, patch) {
    setError('');
    try {
      await api.patch(`/employees/${id}`, patch);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Удалить сотрудника из компании? Его смены будут удалены.')) return;
    setError('');
    try {
      await api.delete(`/employees/${id}`);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  // Раскрыть/скрыть блок доступности сотрудника.
  async function toggleAvailability(id) {
    if (availabilityById[id]) {
      setAvailabilityById({ ...availabilityById, [id]: null });
      return;
    }
    try {
      const { data } = await api.get(`/employees/${id}/availability`);
      setAvailabilityById({ ...availabilityById, [id]: data });
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <section className="card">
      <h2>Сотрудники</h2>
      <p className="text-muted">
        Сотрудники присоединяются сами по коду приглашения (вкладка «Компания»),
        а вы назначаете им филиал и должность.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <table className="table">
        <thead>
          <tr>
            <th>Сотрудник</th>
            <th>Филиал</th>
            <th>Должность</th>
            <th>Активен</th>
            <th className="col-actions">Действия</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((emp) => (
            <Fragment key={emp.id}>
              <tr className={emp.is_active ? '' : 'row-inactive'}>
                <td>
                  <div>{emp.full_name}</div>
                  <div className="text-muted">{emp.email}</div>
                </td>
                <td>
                  <select
                    value={emp.branch_id ?? ''}
                    onChange={(e) =>
                      updateEmployee(emp.id, {
                        branch_id: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                  >
                    <option value="">— не назначен —</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <select
                    value={emp.position_id ?? ''}
                    onChange={(e) =>
                      updateEmployee(emp.id, {
                        position_id: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                  >
                    <option value="">— не назначена —</option>
                    {positions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="checkbox"
                    checked={emp.is_active}
                    onChange={(e) => updateEmployee(emp.id, { is_active: e.target.checked })}
                  />
                </td>
                <td className="col-actions">
                  <button className="btn btn-sm" onClick={() => toggleAvailability(emp.id)}>
                    {availabilityById[emp.id] ? 'Скрыть доступность' : 'Доступность'}
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(emp.id)}>
                    Удалить
                  </button>
                </td>
              </tr>
              {availabilityById[emp.id] && (
                <tr>
                  <td colSpan={5} className="availability-cell">
                    {availabilityById[emp.id].length === 0 ? (
                      <span className="text-muted">Сотрудник не указал доступность.</span>
                    ) : (
                      availabilityById[emp.id].map((a) => (
                        <span key={a.id} className="chip">
                          {WEEKDAYS[a.weekday]} {shortTime(a.start_time)}–{shortTime(a.end_time)}
                        </span>
                      ))
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
          {employees.length === 0 && (
            <tr>
              <td colSpan={5} className="text-muted">
                Пока никто не присоединился. Поделитесь кодом приглашения.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
