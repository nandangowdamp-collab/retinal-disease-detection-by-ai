import { useEffect, useState } from 'react';
import { Eye } from 'lucide-react';
import api, { getApiErrorMessage } from '../../services/api';
import PredictionCard, { getDiseaseBadgeClass } from '../../components/PredictionCard';
import AdminLayout from './AdminLayout';

export default function ManagePredictions() {
  const [predictions, setPredictions] = useState([]);
  const [summary, setSummary] = useState({ total: 0, average_confidence: 0 });
  const [disease, setDisease] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  const loadPredictions = async () => {
    try {
      const { data } = await api.get('/admin/predictions', {
        params: { disease, start_date: startDate, end_date: endDate },
      });
      setPredictions(data.predictions || []);
      setSummary(data.summary || { total: 0, average_confidence: 0 });
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadPredictions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>AI Prediction Monitoring</h1>
          <p>Review platform-wide retinal image classifications and model confidence metrics.</p>
        </div>
        <div className="badge badge-normal">
          Total: {summary.total} • Avg Score: {(summary.average_confidence * 100).toFixed(1)}%
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="filter-bar">
        <select className="form-select" value={disease} onChange={(e) => setDisease(e.target.value)}>
          <option value="all">All Categories</option>
          <option value="Normal">Normal</option>
          <option value="Glaucoma">Glaucoma</option>
          <option value="Hypertensive Retinopathy">Hypertensive Retinopathy</option>
          <option value="Diabetic Retinopathy">Diabetic Retinopathy</option>
        </select>
        <input type="date" className="form-input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" className="form-input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        <button type="button" className="btn btn-primary" onClick={loadPredictions}>Filter</button>
      </div>

      {selected && (
        <div style={{ marginBottom: '1.25rem' }}>
          <PredictionCard prediction={selected} showPatient />
        </div>
      )}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Prediction ID</th>
              <th>Patient</th>
              <th>Category</th>
              <th>Score</th>
              <th>Date</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((p) => (
              <tr key={p.id}>
                <td className="mono">{p.prediction_id}</td>
                <td>{p.patient_name}</td>
                <td><span className={`badge ${getDiseaseBadgeClass(p.predicted_class)}`}>{p.predicted_class}</span></td>
                <td className="mono">{(p.confidence_score * 100).toFixed(2)}%</td>
                <td>{new Date(p.prediction_date).toLocaleString()}</td>
                <td>
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelected(p)}>
                    <Eye size={14} />
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
