import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';

import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';

import PatientDashboard from './pages/patient/PatientDashboard';
import UploadImage from './pages/patient/UploadImage';
import PredictionHistory from './pages/patient/PredictionHistory';
import PatientProfile from './pages/patient/PatientProfile';
import FindDoctor from './pages/patient/FindDoctor';
import PatientMessenger from './pages/patient/PatientMessenger';

import DoctorDashboard from './pages/doctor/DoctorDashboard';
import MyPatients from './pages/doctor/MyPatients';
import PatientDetails from './pages/doctor/PatientDetails';
import Consultations from './pages/doctor/Consultations';
import DoctorProfile from './pages/doctor/DoctorProfile';
import DoctorMessenger from './pages/doctor/DoctorMessenger';

import AdminDashboard from './pages/admin/AdminDashboard';
import ManagePatients from './pages/admin/ManagePatients';
import ManageDoctors from './pages/admin/ManageDoctors';
import ManagePredictions from './pages/admin/ManagePredictions';
import ManageConsultations from './pages/admin/ManageConsultations';
import ManageUsers from './pages/admin/ManageUsers';
import SystemReports from './pages/admin/SystemReports';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Navbar />
          <div style={{ flex: 1 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Patient Portal */}
              <Route path="/patient/dashboard" element={<ProtectedRoute allowedRoles={['patient']}><PatientDashboard /></ProtectedRoute>} />
              <Route path="/patient/upload" element={<ProtectedRoute allowedRoles={['patient']}><UploadImage /></ProtectedRoute>} />
              <Route path="/patient/history" element={<ProtectedRoute allowedRoles={['patient']}><PredictionHistory /></ProtectedRoute>} />
              <Route path="/patient/doctors" element={<ProtectedRoute allowedRoles={['patient']}><FindDoctor /></ProtectedRoute>} />
              <Route path="/patient/messenger" element={<ProtectedRoute allowedRoles={['patient']}><PatientMessenger /></ProtectedRoute>} />
              <Route path="/patient/profile" element={<ProtectedRoute allowedRoles={['patient']}><PatientProfile /></ProtectedRoute>} />

              {/* Doctor Portal */}
              <Route path="/doctor/dashboard" element={<ProtectedRoute allowedRoles={['doctor']}><DoctorDashboard /></ProtectedRoute>} />
              <Route path="/doctor/patients" element={<ProtectedRoute allowedRoles={['doctor']}><MyPatients /></ProtectedRoute>} />
              <Route path="/doctor/patients/:patientId" element={<ProtectedRoute allowedRoles={['doctor']}><PatientDetails /></ProtectedRoute>} />
              <Route path="/doctor/consultations" element={<ProtectedRoute allowedRoles={['doctor']}><Consultations /></ProtectedRoute>} />
              <Route path="/doctor/messenger" element={<ProtectedRoute allowedRoles={['doctor']}><DoctorMessenger /></ProtectedRoute>} />
              <Route path="/doctor/profile" element={<ProtectedRoute allowedRoles={['doctor']}><DoctorProfile /></ProtectedRoute>} />

              {/* Admin Portal */}
              <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
              <Route path="/admin/patients" element={<ProtectedRoute allowedRoles={['admin']}><ManagePatients /></ProtectedRoute>} />
              <Route path="/admin/doctors" element={<ProtectedRoute allowedRoles={['admin']}><ManageDoctors /></ProtectedRoute>} />
              <Route path="/admin/predictions" element={<ProtectedRoute allowedRoles={['admin']}><ManagePredictions /></ProtectedRoute>} />
              <Route path="/admin/consultations" element={<ProtectedRoute allowedRoles={['admin']}><ManageConsultations /></ProtectedRoute>} />
              <Route path="/admin/users" element={<ProtectedRoute allowedRoles={['admin']}><ManageUsers /></ProtectedRoute>} />
              <Route path="/admin/reports" element={<ProtectedRoute allowedRoles={['admin']}><SystemReports /></ProtectedRoute>} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
