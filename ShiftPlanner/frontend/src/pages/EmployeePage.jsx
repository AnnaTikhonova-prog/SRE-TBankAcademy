import { useState } from 'react';
import api, { errorText } from '../api.js';
import { useAuth } from '../auth.jsx';
import Layout from '../components/Layout.jsx';
import MyShiftsTab from '../components/MyShiftsTab.jsx';
import AvailabilityTab from '../components/AvailabilityTab.jsx';
import ProfileTab from '../components/ProfileTab.jsx';

const TABS = [
  { id: 'shifts', label: 'Мои смены' },
  { id: 'availability', label: 'Моя доступность' },
  { id: 'profile', label: 'Профиль' },
];

// Панель сотрудника. Если сотрудник ещё не в компании — показываем
// форму вступления по коду приглашения вместо вкладок.
export default function EmployeePage() {
  const { user, refreshUser } = useAuth();
  const [tab, setTab] = useState('shifts');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const hasCompany = Boolean(user?.employee);

  async function handleJoin(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await api.post('/companies/join', { invite_code: inviteCode.trim() });
      await refreshUser();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout
      title="Личный кабинет сотрудника"
      tabs={hasCompany ? TABS : null}
      activeTab={tab}
      onTabChange={setTab}
    >
      {!hasCompany ? (
        <section className="card card-narrow">
          <h2>Присоединение к компании</h2>
          <p className="text-muted">
            Попросите у менеджера код приглашения и введите его ниже.
          </p>
          <form onSubmit={handleJoin} className="form">
            <label className="field">
              <span>Код приглашения</span>
              <input
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
                required
                placeholder="Например: COFFEE42"
              />
            </label>
            {error && <div className="alert alert-error">{error}</div>}
            <button className="btn btn-primary" disabled={busy}>
              {busy ? 'Проверка…' : 'Присоединиться'}
            </button>
          </form>
        </section>
      ) : (
        <>
          {tab === 'shifts' && <MyShiftsTab />}
          {tab === 'availability' && <AvailabilityTab />}
          {tab === 'profile' && <ProfileTab />}
        </>
      )}
    </Layout>
  );
}
