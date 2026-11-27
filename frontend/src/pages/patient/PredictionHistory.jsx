import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, Eye } from 'lucide-react';
import PredictionCard, { getDiseaseBadgeClass } from '../../components/PredictionCard';
import { getApiErrorMessage } from '../../services/api';
import { predictionService } from '../../services/predictionService';
import PatientLayout from './PatientLayout';

export default function PredictionHistory() {
  const navigate = useNavigate();
  const [predictions, setPredictions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [disease, setDisease] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await predictionService.getHistory({
        search,
        disease,
        start_date: startDate,
        end_date: endDate,
      });
      setPredictions(data.predictions || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>Prediction History</h1>
          <p>Search past retinal scans, inspect class probabilities, and download PDF reports.</p>
        </div>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search ID, filename, or class..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="form-select" value={disease} onChange={(e) => setDisease(e.target.value)}>
          <option value="all">All Categories</option>
          <option value="Normal">Normal</option>
          <option value="Glaucoma">Glaucoma</option>
          <option value="Hypertensive Retinopathy">Hypertensive Retinopathy</option>
          <option value="Diabetic Retinopathy">Diabetic Retinopathy</option>
        </select>
        <input type="date" className="form-input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" className="form-input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        <button type="button" className="btn btn-primary" onClick={fetchHistory}>
          Apply Filters
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {selected && (
        <div style={{ marginBottom: '1.5rem' }}>
          <PredictionCard
            prediction={selected}
            onConsultDoctor={(pred) => navigate(`/patient/doctors?predictionId=${pred.id}`)}
          />
        </div>
      )}

      {loading ? (
        <div className="spinner" />
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Prediction ID</th>
                <th>Date</th>
                <th>Predicted Category</th>
                <th>Model Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {predictions.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                    No prediction records found.
                  </td>
                </tr>
              ) : (
                predictions.map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.prediction_id}</td>
                    <td>{new Date(p.prediction_date).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${getDiseaseBadgeClass(p.predicted_class)}`}>
                        {p.predicted_class}
                      </span>
                    </td>
                    <td className="mono">{(p.confidence_score * 100).toFixed(2)}%</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.45rem' }}>
                        <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelected(p)}>
                          <Eye size={14} />
                          View
                        </button>
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={() => predictionService.downloadReportPdf(p.id, `${p.prediction_id}.pdf`)}
                        >
                          <Download size={14} />
                          PDF
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </PatientLayout>
  );
}
