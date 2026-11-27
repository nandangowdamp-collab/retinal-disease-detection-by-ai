import { LayoutDashboard, Upload, History, Stethoscope, MessageSquare, User } from 'lucide-react';
import Sidebar from '../../components/Sidebar';

const patientLinks = [
  { to: '/patient/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/patient/upload', label: 'Upload Retinal Scan', icon: Upload },
  { to: '/patient/history', label: 'Prediction History', icon: History },
  { to: '/patient/doctors', label: 'Find Doctor & Consult', icon: Stethoscope },
  { to: '/patient/messenger', label: 'Doctor Messenger', icon: MessageSquare },
  { to: '/patient/profile', label: 'My Profile', icon: User },
];

export default function PatientLayout({ children }) {
  return (
    <div className="dashboard-shell portal-patient">
      <Sidebar title="Patient Portal" links={patientLinks} />
      <main className="dashboard-main">{children}</main>
    </div>
  );
}
