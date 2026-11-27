import { LayoutDashboard, Users, CalendarCheck, MessageSquare, UserCog } from 'lucide-react';
import Sidebar from '../../components/Sidebar';

const doctorLinks = [
  { to: '/doctor/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/doctor/patients', label: 'My Patients', icon: Users },
  { to: '/doctor/consultations', label: 'Consultations', icon: CalendarCheck },
  { to: '/doctor/messenger', label: 'Patient Messenger', icon: MessageSquare },
  { to: '/doctor/profile', label: 'Doctor Profile', icon: UserCog },
];

export default function DoctorLayout({ children }) {
  return (
    <div className="dashboard-shell portal-doctor">
      <Sidebar title="Doctor Portal" links={doctorLinks} />
      <main className="dashboard-main">{children}</main>
    </div>
  );
}
