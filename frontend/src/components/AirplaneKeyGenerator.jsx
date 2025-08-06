import React, { useState } from 'react';
import '../App.css';

const AirplaneKeyGenerator = () => {
  const [airplaneName, setAirplaneName] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const generateKey = async () => {
    setPublicKey('');
    setError('');

    if (!airplaneName.trim()) {
      setError('Please enter an airplane name.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/generate-airplane-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ airplane_name: airplaneName.trim() }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to generate key');
      }

      const data = await response.json();
      
      if (data.public_key_pem) {
        setPublicKey(data.public_key_pem);
      } else {
        setPublicKey('');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Generate Airplane Key Pair</h2>

      <input
        type="text"
        placeholder="Enter airplane name"
        value={airplaneName}
        onChange={(e) => setAirplaneName(e.target.value)}
      />

      <button onClick={generateKey} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Key'}
      </button>

      {publicKey && (
        <>
          <h4>Public Key for "{airplaneName.trim()}":</h4>
          <textarea
            rows={10}
            cols={60}
            readOnly
            style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}
            value={publicKey}
          />
        </>
      )}

      {error && <p className="error">❌ {error}</p>}
    </div>
  );
};

export default AirplaneKeyGenerator;