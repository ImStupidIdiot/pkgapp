import React, { useState, useEffect } from 'react';
import '../App.css';

const DecryptSoftwareUploader = () => {
  const [packageFile, setPackageFile] = useState(null);
  const [airplaneKeyName, setAirplaneKeyName] = useState('');
  const [clientKeyName, setClientKeyName] = useState('');
  const [airplaneKeys, setAirplaneKeys] = useState([]);
  const [clientKeys, setClientKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchAirplaneKeys = async () => {
    try {
      const res = await fetch('/list-airplane-keys');
      const data = await res.json();
      if (res.ok) setAirplaneKeys(data.keys || []);
    } catch {
      // silently fail
    }
  };

  const fetchClientKeys = async () => {
    try {
      const res = await fetch('/list-client-keys');
      const data = await res.json();
      if (res.ok) setClientKeys(data.keys || []);
    } catch {
      // silently fail
    }
  };

  useEffect(() => {
    fetchAirplaneKeys();
    fetchClientKeys();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!packageFile) {
      setError('Please upload an encrypted package');
      return;
    }
    if (!airplaneKeyName) {
      setError('Please select an airplane key');
      return;
    }
    if (!clientKeyName) {
      setError('Please select a client key');
      return;
    }

    const formData = new FormData();
    formData.append('file', packageFile);
    formData.append('airplane_key_name', airplaneKeyName);
    formData.append('client_key_name', clientKeyName);

    setLoading(true);
    try {
      const res = await fetch('/decrypt-software', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Decryption failed');
      }

      const blob = await res.blob();

      // Extract filename from Content-Disposition header
      const disposition = res.headers.get('Content-Disposition');
      let filename = 'decrypted_file';
      if (disposition && disposition.includes('filename=')) {
        filename = disposition
          .split('filename=')[1]
          .replace(/["']/g, '') // remove quotes
          .trim();
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Decrypt Software Package</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Encrypted Package (.zip):</label>
          <input
            type="file"
            onChange={(e) => setPackageFile(e.target.files[0])}
          />
        </div>

        <div className="form-group">
          <label>Airplane Key:</label>
          <select
            value={airplaneKeyName}
            onClick={fetchAirplaneKeys}
            onChange={(e) => setAirplaneKeyName(e.target.value)}
          >
            <option value="">-- Select Airplane Key --</option>
            {airplaneKeys.map((key) => (
              <option key={key} value={key}>{key}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Client Key:</label>
          <select
            value={clientKeyName}
            onClick={fetchClientKeys}
            onChange={(e) => setClientKeyName(e.target.value)}
          >
            <option value="">-- Select Client Key --</option>
            {clientKeys.map((key) => (
              <option key={key} value={key}>{key}</option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Decrypting...' : 'Decrypt'}
        </button>
      </form>

      {error && <p className="error">❌ {error}</p>}
    </div>
  );
};

export default DecryptSoftwareUploader;