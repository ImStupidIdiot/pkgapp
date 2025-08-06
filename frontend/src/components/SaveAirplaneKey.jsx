import React, { useState } from 'react';
import '../App.css';

const SaveAirplaneKey = () => {
  const [name, setName] = useState('');
  const [publicKeyPem, setPublicKeyPem] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSave = async () => {
    setError('');
    setMessage('');

    if (!name.trim()) {
      setError('Please enter a key name.');
      return;
    }
    if (!publicKeyPem.trim()) {
      setError('Please paste the public key PEM.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/save-airplane-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, public_key_pem: publicKeyPem }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to save key');
      setMessage(data.message);
      setName('');
      setPublicKeyPem('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Save Airplane Public Key</h2>

      <label>Key Name:</label>
      <input
        type="text"
        placeholder="e.g. PlaneX"
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={loading}
      />

      <label>Public Key PEM:</label>
      <textarea
        rows={10}
        placeholder="Paste the full public key PEM here"
        value={publicKeyPem}
        onChange={(e) => setPublicKeyPem(e.target.value)}
        disabled={loading}
      />

      <button onClick={handleSave} disabled={loading}>
        {loading ? 'Saving...' : 'Save Key'}
      </button>

      {message && <p className="success">✅ {message}</p>}
      {error && <p className="error">❌ {error}</p>}
    </div>
  );
};

export default SaveAirplaneKey;