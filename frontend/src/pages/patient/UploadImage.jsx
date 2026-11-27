import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ImageUploader from '../../components/ImageUploader';
import PredictionCard from '../../components/PredictionCard';
import { getApiErrorMessage } from '../../services/api';
import { predictionService } from '../../services/predictionService';
import PatientLayout from './PatientLayout';

export default function UploadImage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState(null);

  const handleClassify = async (file) => {
    setError('');
    setPrediction(null);
    setLoading(true);
    try {
      const data = await predictionService.classifyImage(file);
      setPrediction(data.prediction);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Classification failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>Retinal Image Upload &amp; AI Classification</h1>
          <p>Upload a fundus photograph to screen for Normal, Glaucoma, Hypertensive Retinopathy, or Diabetic Retinopathy.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <ImageUploader onClassify={handleClassify} loading={loading} />
        {prediction && (
          <PredictionCard
            prediction={prediction}
            onConsultDoctor={(pred) => navigate(`/patient/doctors?predictionId=${pred.id}`)}
          />
        )}
      </div>
    </PatientLayout>
  );
}
