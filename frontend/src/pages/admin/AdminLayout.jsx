import {
  Activity,
  CalendarCheck,
  FileBarChart,
  LayoutDashboard,
  ShieldCheck,
  Stethoscope,
  UserCog,
  Users,
} from 'lucide-react';
import Sidebar from '../../components/Sidebar';

const adminLinks = [
  { to: '/admin/dashboard', label: 'Overview & Stats', icon: LayoutDashboard },
  { to: '/admin/patients', label: 'Manage Patients', icon: Users },
  { to: '/admin/doctors', label: 'Manage Doctors', icon: Stethoscope },
  { to: '/admin/predictions', label: 'AI Predictions', icon: Activity },
  { to: '/admin/consultations', label: 'Consultations', icon: CalendarCheck },
  { to: '/admin/users', label: 'User Accounts', icon: UserCog },
  { to: '/admin/reports', label: 'Audit & Settings', icon: FileBarChart },
];

export default function AdminLayout({ children }) {
  return (
    <div className="dashboard-shell portal-admin">
      <Sidebar title="Admin Portal" links={adminLinks} />
      <main className="dashboard-main">{children}</main>
    </div>
  );
}
