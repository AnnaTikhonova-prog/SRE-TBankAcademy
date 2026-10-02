import { useState } from 'react';
import { useAuth } from '../auth.jsx';
import Layout from '../components/Layout.jsx';
import CompanyTab from '../components/CompanyTab.jsx';
import BranchesTab from '../components/BranchesTab.jsx';
import PositionsTab from '../components/PositionsTab.jsx';
import EmployeesTab from '../components/EmployeesTab.jsx';
import ShiftsTab from '../components/ShiftsTab.jsx';

const TABS = [
  { id: 'company', label: 'Компания' },
  { id: 'branches', label: 'Филиалы' },
  { id: 'positions', label: 'Должности' },
  { id: 'employees', label: 'Сотрудники' },
  { id: 'shifts', label: 'Смены' },
];

// Панель менеджера: управление компанией и CRUD по всем сущностям.
export default function ManagerPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState('company');
  const hasCompany = Boolean(user?.company);

  return (
    <Layout title="Панель менеджера" tabs={TABS} activeTab={tab} onTabChange={setTab}>
      {!hasCompany && tab !== 'company' ? (
        <div className="alert alert-info">
          Сначала создайте компанию на вкладке «Компания».
        </div>
      ) : (
        <>
          {tab === 'company' && <CompanyTab />}
          {tab === 'branches' && <BranchesTab />}
          {tab === 'positions' && <PositionsTab />}
          {tab === 'employees' && <EmployeesTab />}
          {tab === 'shifts' && <ShiftsTab />}
        </>
      )}
    </Layout>
  );
}
