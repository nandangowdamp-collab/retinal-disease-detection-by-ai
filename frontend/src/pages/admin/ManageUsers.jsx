import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';

export default function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [role, setRole] = useState('all');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadUsers = async () => {
    try {
      const { data } = await api.get('/admin/users', { params: { role } });
      setUsers(data.users || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  const toggleStatus = async (user) => {
    const next = user.account_status === 'active' ? 'inactive' : 'active';
    try {
      await api.put(`/admin/users/${user.id}/status`, { account_status: next });
      setNotice(`Account for ${user.email} is now ${next}.`);
      loadUsers();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>User Account Directory</h1>
          <p>Manage platform accounts across patient, doctor, and administrator roles.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="filter-bar">
        <select className="form-select" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="all">All Roles</option>
          <option value="patient">Patients</option>
          <option value="doctor">Doctors</option>
          <option value="admin">Admins</option>
        </select>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Full Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td style={{ textTransform: 'capitalize' }}>{u.role}</td>
                <td><span className={`badge badge-${u.account_status}`}>{u.account_status}</span></td>
                <td>
                  {u.role !== 'admin' && (
                    <button
                      type="button"
                      className={`btn btn-sm ${u.account_status === 'active' ? 'btn-danger' : 'btn-primary'}`}
                      onClick={() => toggleStatus(u)}
                    >
                      {u.account_status === 'active' ? 'Deactivate' : 'Activate'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
