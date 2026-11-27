import { useRef, useState } from 'react';
import { ImagePlus, UploadCloud, X } from 'lucide-react';

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];
const MAX_BYTES = 10 * 1024 * 1024;

export default function ImageUploader({ onClassify, loading }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleSelectFile = (selected) => {
    setValidationError('');
    if (!selected) return;

    const ext = selected.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(selected.type) && !['jpg', 'jpeg', 'png'].includes(ext)) {
      setValidationError('Unsupported format. Please select a JPG, JPEG, or PNG retinal fundus image.');
      return;
    }
    if (selected.size > MAX_BYTES) {
      setValidationError('File size exceeds the 10 MB limit.');
      return;
    }

    if (preview) URL.revokeObjectURL(preview);
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  };

  const clearSelection = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setValidationError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="card">
      <h3 style={{ marginBottom: '0.5rem' }}>Upload Retinal Fundus Image</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: 0 }}>
        Supported formats: JPG, JPEG, PNG (max 10 MB). Images are preprocessed to RGB and evaluated across 4 classes.
      </p>

      {validationError && <div className="alert alert-error">{validationError}</div>}

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        style={{ display: 'none' }}
        onChange={(e) => handleSelectFile(e.target.files?.[0])}
      />

      {!preview ? (
        <div
          className={`upload-dropzone ${dragging ? 'dragging' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleSelectFile(e.dataTransfer.files?.[0]);
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <UploadCloud size={38} color="#0d9488" style={{ marginBottom: '0.6rem' }} />
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
            Drag &amp; drop a retinal fundus image here, or click to browse
          </div>
          <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            JPG, JPEG, PNG up to 10 MB
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <img src={preview} alt="Retinal fundus preview" className="fundus-preview" />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              <ImagePlus size={16} style={{ verticalAlign: 'text-bottom', marginRight: 6 }} />
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </span>
            <div style={{ display: 'flex', gap: '0.6rem' }}>
              <button type="button" className="btn btn-secondary btn-sm" onClick={clearSelection} disabled={loading}>
                <X size={15} />
                Remove
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={loading}
                onClick={() => onClassify(file)}
              >
                {loading ? 'Analyzing Retinal Scan...' : 'Run AI Classification'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
