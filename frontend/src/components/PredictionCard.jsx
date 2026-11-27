import { Download, Stethoscope } from 'lucide-react';
import { predictionService } from '../services/predictionService';
import SecureRetinalImage from './SecureRetinalImage';

const CLASS_COLORS = {
  Normal: '#059669',
  Glaucoma: '#d97706',
  'Hypertensive Retinopathy': '#7c3aed',
  'Diabetic Retinopathy': '#dc2626',
};

export function getDiseaseBadgeClass(disease) {
  if (disease === 'Normal') return 'badge-normal';
  if (disease === 'Glaucoma') return 'badge-glaucoma';
  if (disease === 'Hypertensive Retinopathy') return 'badge-hypertensive';
  return 'badge-diabetic';
}

export default function PredictionCard({ prediction, onConsultDoctor, showPatient = false }) {
  if (!prediction) return null;

  const scores = prediction.class_scores || {};
  const confidencePct = ((prediction.confidence_score || 0) * 100).toFixed(2);

  const handleDownload = () => {
    predictionService.downloadReportPdf(
      prediction.id,
      `${prediction.prediction_id || 'retinal-report'}.pdf`
    );
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
        <div>
          <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {prediction.prediction_id}
          </span>
          <h3 style={{ marginTop: '0.2rem' }}>AI Screening Result</h3>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            {prediction.prediction_date ? new Date(prediction.prediction_date).toLocaleString() : ''}
            {showPatient && prediction.patient_name ? ` • Patient: ${prediction.patient_name}` : ''}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleDownload}>
            <Download size={15} />
            Download PDF Report
          </button>
          {onConsultDoctor && (
            <button type="button" className="btn btn-primary btn-sm" onClick={() => onConsultDoctor(prediction)}>
              <Stethoscope size={15} />
              Consult Doctor
            </button>
          )}
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div>
          <SecureRetinalImage predictionId={prediction.id} alt={`Retinal scan ${prediction.prediction_id}`} />
        </div>

        <div>
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 10, border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Predicted Category
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
              <span className={`badge ${getDiseaseBadgeClass(prediction.predicted_class)}`} style={{ fontSize: '0.9rem', padding: '0.35rem 0.85rem' }}>
                {prediction.predicted_class}
              </span>
              <span style={{ fontWeight: 700, fontSize: '1.15rem' }}>
                {confidencePct}% <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>model score</span>
              </span>
            </div>
          </div>

          <h4 style={{ fontSize: '0.92rem', marginBottom: '0.65rem' }}>Class Score Distribution</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {Object.entries(scores).map(([clsName, val]) => {
              const pct = Math.max(0, Math.min(100, Number(val) * 100));
              return (
                <div key={clsName}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '0.22rem' }}>
                    <span>{clsName}</span>
                    <span className="mono">{pct.toFixed(2)}%</span>
                  </div>
                  <div className="prob-bar-track">
                    <div
                      className="prob-bar-fill"
                      style={{
                        width: `${pct}%`,
                        background: CLASS_COLORS[clsName] || '#0284c7',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {prediction.doctor_assessment && (
        <div className="alert alert-info" style={{ marginTop: '1rem', marginBottom: 0 }}>
          <div>
            <strong>Doctor Assessment ({prediction.doctor_assessment.doctor_name}):</strong>{' '}
            <span>{prediction.doctor_assessment.clinical_impression}</span>
            {prediction.doctor_assessment.assessment_notes && (
              <div style={{ marginTop: '0.25rem' }}>{prediction.doctor_assessment.assessment_notes}</div>
            )}
          </div>
        </div>
      )}

      <div className="alert alert-warning" style={{ marginTop: '1rem', marginBottom: 0, fontSize: '0.82rem' }}>
        <span>
          <strong>Decision-Support Notice:</strong> AI confidence scores are model outputs for educational and screening support only, not confirmed clinical diagnoses. Consult a qualified eye specialist.
        </span>
      </div>
    </div>
  );
}
