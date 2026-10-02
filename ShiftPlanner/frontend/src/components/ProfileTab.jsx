import { useAuth } from '../auth.jsx';

// Вкладка «Профиль»: данные учётной записи и место работы.
export default function ProfileTab() {
  const { user } = useAuth();

  return (
    <section className="card card-narrow">
      <h2>Профиль</h2>
      <dl className="profile-list">
        <dt>Имя</dt>
        <dd>{user.full_name}</dd>
        <dt>Email</dt>
        <dd>{user.email}</dd>
        <dt>Роль</dt>
        <dd>Сотрудник</dd>
        {user.company && (
          <>
            <dt>Компания</dt>
            <dd>{user.company.name}</dd>
          </>
        )}
      </dl>
      <p className="text-muted">
        Филиал и должность назначает менеджер на вкладке «Сотрудники».
      </p>
    </section>
  );
}
