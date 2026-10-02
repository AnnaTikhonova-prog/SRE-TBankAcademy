import { useCallback, useEffect, useState } from 'react';
import api, { errorText, formatDate, shortTime } from '../api.js';

const EMPTY_FORM = {
  employee_id: '',
  branch_id: '',
  position_id: '',
  shift_date: '',
  start_time: '',
  end_time: '',
};

// Вкладка «Смены»: менеджер вручную назначает смены сотрудникам.
// Бэкенд проверяет, что смены одного сотрудника не пересекаются.
export default function ShiftsTab() {
  const [shifts, setShifts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [branches, setBranches] = useState([]);
  const [positions, setPositions] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [error, setError] = useState('');

  // Справочники для выпадающих списков.
  const loadRefs = useCallback(async () => {
    const [emp, br, pos] = await Promise.all([
      api.get('/employees/'),
      api.get('/branches/'),
      api.get('/positions/'),
    ]);
    setEmployees(emp.data);
    setBranches(br.data);
    setPositions(pos.data);
  }, []);

  const loadShifts = useCallback(async () => {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    const { data } = await api.get('/shifts/', { params });
    setShifts(data);
  }, [dateFrom, dateTo]);

  useEffect(() => {
    loadRefs().catch((err) => setError(errorText(err)));
  }, [loadRefs]);

  useEffect(() => {
    loadShifts().catch((err) => setError(errorText(err)));
  }, [loadShifts]);

  // Приводит форму к телу запроса API (числовые id, пустые значения -> null).
  function toPayload(f) {
    return {
      employee_id: Number(f.employee_id),
      branch_id: Number(f.branch_id),
      position_id: Number(f.position_id),
      shift_date: f.shift_date,
      start_time: f.start_time,
      end_time: f.end_time,
    };
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.post('/shifts/', toPayload(form));
      setForm(EMPTY_FORM);
      await loadShifts();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleUpdate(e) {
    e.preventDefault();
    setError('');
    try {
      await api.patch(`/shifts/${editId}`, toPayload(editForm));
      setEditId(null);
      await loadShifts();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Удалить смену?')) return;
    setError('');
    try {
      await api.delete(`/shifts/${id}`);
      await loadShifts();
    } catch (err) {
      setError(errorText(err));
    }
  }

  const set = (setter, obj, field) => (e) => setter({ ...obj, [field]: e.target.value });

  // Форма создания/редактирования смены (одна разметка на оба случая).
  function shiftForm(f, setter, onSubmit, submitLabel, onCancel) {
    return (
      <form onSubmit={onSubmit} className="form form-grid">
        <label className="field">
          <span>Сотрудник</span>
          <select value={f.employee_id} onChange={set(setter, f, 'employee_id')} required>
            <option value="">— выберите —</option>
            {employees
              .filter((e) => e.is_active)
              .map((e) => (
                <option key={e.id} value={e.id}>
                  {e.full_name}
                </option>
              ))}
          </select>
        </label>
        <label className="field">
          <span>Филиал</span>
          <select value={f.branch_id} onChange={set(setter, f, 'branch_id')} required>
            <option value="">— выберите —</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Должность</span>
          <select value={f.position_id} onChange={set(setter, f, 'position_id')} required>
            <option value="">— выберите —</option>
            {positions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Дата</span>
          <input
            type="date"
            value={f.shift_date}
            onChange={set(setter, f, 'shift_date')}
            required
          />
        </label>
        <label className="field">
          <span>Начало</span>
          <input
            type="time"
            value={f.start_time}
            onChange={set(setter, f, 'start_time')}
            required
          />
        </label>
        <label className="field">
          <span>Конец</span>
          <input
            type="time"
            value={f.end_time}
            onChange={set(setter, f, 'end_time')}
            required
          />
        </label>
        <div className="btn-row">
          <button className="btn btn-primary">{submitLabel}</button>
          {onCancel && (
            <button type="button" className="btn btn-ghost" onClick={onCancel}>
              Отмена
            </button>
          )}
        </div>
      </form>
    );
  }

  return (
    <section className="card">
      <h2>Смены</h2>

      <details className="create-panel">
        <summary className="btn btn-primary">Назначить смену</summary>
        {shiftForm(form, setForm, handleCreate, 'Создать смену', null)}
      </details>

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
            <th>Сотрудник</th>
            <th>Должность</th>
            <th>Филиал</th>
            <th className="col-actions">Действия</th>
          </tr>
        </thead>
        <tbody>
          {shifts.map((shift) => (
            <tr key={shift.id}>
              {editId === shift.id ? (
                <td colSpan={6}>
                  {shiftForm(
                    editForm,
                    setEditForm,
                    handleUpdate,
                    'Сохранить',
                    () => setEditId(null),
                  )}
                </td>
              ) : (
                <>
                  <td>{formatDate(shift.shift_date)}</td>
                  <td>
                    {shortTime(shift.start_time)}–{shortTime(shift.end_time)}
                  </td>
                  <td>{shift.employee_name}</td>
                  <td>{shift.position_name}</td>
                  <td>{shift.branch_name}</td>
                  <td className="col-actions">
                    <button
                      className="btn btn-sm"
                      onClick={() => {
                        setEditId(shift.id);
                        setEditForm({
                          employee_id: String(shift.employee_id),
                          branch_id: String(shift.branch_id),
                          position_id: String(shift.position_id),
                          shift_date: shift.shift_date,
                          start_time: shortTime(shift.start_time),
                          end_time: shortTime(shift.end_time),
                        });
                      }}
                    >
                      Изменить
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(shift.id)}>
                      Удалить
                    </button>
                  </td>
                </>
              )}
            </tr>
          ))}
          {shifts.length === 0 && (
            <tr>
              <td colSpan={6} className="text-muted">
                Смен за выбранный период нет.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
