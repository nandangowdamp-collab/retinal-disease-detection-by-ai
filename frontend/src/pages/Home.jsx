import { Link } from 'react-router-dom';
import {
  Activity,
  Brain,
  CheckCircle2,
  FileText,
  MessageSquare,
  ShieldCheck,
  Stethoscope,
  Upload,
} from 'lucide-react';

const DISEASES = [
  {
    name: 'Normal',
    badge: 'badge-normal',
    desc: 'Retinal fundus scan without detected abnormalities associated with the target screening categories.',
  },
  {
    name: 'Glaucoma',
    badge: 'badge-glaucoma',
    desc: 'Screening for optic nerve head structural changes commonly associated with elevated intraocular pressure.',
  },
  {
    name: 'Hypertensive Retinopathy',
    badge: 'badge-hypertensive',
    desc: 'Identifies vascular narrowing and retinal microvascular changes linked to systemic hypertension.',
  },
  {
    name: 'Diabetic Retinopathy',
    badge: 'badge-diabetic',
    desc: 'Detects retinal microaneurysms, exudates, and vascular lesions associated with diabetes mellitus.',
  },
];

export default function Home() {
  return (
    <div>
      <section className="hero-section">
        <div className="container hero-grid">
          <div>
            <span className="badge badge-normal" style={{ fontSize: '0.8rem' }}>
              TensorFlow / Keras Clinical Decision-Support Prototype
            </span>
            <h1 className="hero-title">
              AI-Based Retinal Image Classification for Early Detection of Eye Diseases
            </h1>
            <p className="hero-subtitle">
              A secure three-portal screening platform connecting patients, verified ophthalmologists,
              and administrators through automated four-class retinal fundus analysis, PDF reporting,
              and real-time Socket.IO consultation.
            </p>
            <div style={{ display: 'flex', gap: '0.85rem', flexWrap: 'wrap' }}>
              <Link to="/register" className="btn btn-primary">
                Register as Patient or Doctor
              </Link>
              <Link to="/login" className="btn btn-secondary">
                Portal Sign In
              </Link>
            </div>
          </div>

          <div className="card" style={{ padding: '1.6rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Target Classification Categories</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {DISEASES.map((d, idx) => (
                <div
                  key={d.name}
                  style={{
                    padding: '0.85rem',
                    borderRadius: 10,
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                    <strong>
                      {idx + 1}. {d.name}
                    </strong>
                    <span className={`badge ${d.badge}`}>{d.name.split(' ')[0]}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{d.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section style={{ padding: '3.5rem 1.5rem' }}>
        <div className="container">
          <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Three Integrated Healthcare Portals</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.75rem' }}>
            Role-based access control across Patient, Doctor, and Administrator workflows.
          </p>

          <div className="grid-3">
            <div className="card">
              <Upload size={26} color="#0d9488" style={{ marginBottom: '0.75rem' }} />
              <h3 style={{ marginBottom: '0.4rem' }}>Patient Portal</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Upload retinal fundus images, review 4-class AI confidence scores, download PDF screening
                reports, request consultations, and chat directly with verified doctors.
              </p>
            </div>

            <div className="card">
              <Stethoscope size={26} color="#1d4ed8" style={{ marginBottom: '0.75rem' }} />
              <h3 style={{ marginBottom: '0.4rem' }}>Doctor Portal</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Admin-verified specialists manage assigned patients, inspect uploaded scans, record
                separate clinical assessments, accept or reject consultations, and message patients live.
              </p>
            </div>

            <div className="card">
              <ShieldCheck size={26} color="#4338ca" style={{ marginBottom: '0.75rem' }} />
              <h3 style={{ marginBottom: '0.4rem' }}>Admin Portal</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Verify doctor credentials, monitor AI classification statistics, manage users and
                consultations, inspect audit logs, and moderate reported conversations.
              </p>
            </div>
          </div>

          <div className="grid-3" style={{ marginTop: '1.25rem' }}>
            <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <Brain size={22} color="#0284c7" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <strong>CNN Transfer Learning Pipeline</strong>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                  Validates RGB input shape and softmax output strictly against your trained Keras model.
                </p>
              </div>
            </div>
            <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <MessageSquare size={22} color="#0d9488" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <strong>Real-Time Socket.IO Messenger</strong>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                  Instant delivery, unread counts, presence indicators, and server-verified participant security.
                </p>
              </div>
            </div>
            <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <FileText size={22} color="#4338ca" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <strong>Downloadable PDF Reports</strong>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                  Export structured patient screening reports with scores, fundus preview, and clinician notes.
                </p>
              </div>
            </div>
          </div>

          <div className="alert alert-warning" style={{ marginTop: '2rem' }}>
            <Activity size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>
              <strong>Important Clinical Disclaimer:</strong> This application is an educational and clinical
              decision-support prototype, not a replacement for professional eye examination or diagnosis. AI
              confidence scores must not be presented as confirmed disease probabilities.
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
