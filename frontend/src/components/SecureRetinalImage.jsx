import { useEffect, useState } from 'react';
import { predictionService } from '../services/predictionService';

export default function SecureRetinalImage({ predictionId, alt = 'Retinal fundus scan', className = 'fundus-preview', style = {} }) {
  const [objectUrl, setObjectUrl] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    let createdUrl = null;
    if (!predictionId) return undefined;

    setError(false);
    predictionService
      .fetchProtectedImageUrl(predictionId)
      .then((url) => {
        if (!active) {
          URL.revokeObjectURL(url);
          return;
        }
        createdUrl = url;
        setObjectUrl(url);
      })
      .catch(() => {
        if (active) setError(true);
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [predictionId]);

  if (error) {
    return (
      <div style={{ padding: '1.5rem', textAlign: 'center', background: '#f1f5f9', borderRadius: 8, color: '#64748b', ...style }}>
        Image unavailable
      </div>
    );
  }

  if (!objectUrl) {
    return (
      <div style={{ padding: '2rem', display: 'grid', placeItems: 'center', background: '#f8fafc', borderRadius: 8, ...style }}>
        <div className="spinner" />
      </div>
    );
  }

  return <img src={objectUrl} alt={alt} className={className} style={style} />;
}
