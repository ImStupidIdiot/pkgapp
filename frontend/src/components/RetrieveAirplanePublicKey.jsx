import React, { useState } from 'react';
import '../App.css';

const RetrieveAirplanePublicKey = () => {
  const [airplaneName, setAirplaneName] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [error, setError] = useState('');

  const handleRetrieve = async () => {
    setError('');
    setPublicKey('');

    if (!airplaneName) {
      setError('Please enter an airplane name');
      return;
    }

    try {
      const res = await fetch(`/retrieve-airplane-public-key/${airplaneName}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to retrieve key');
      }

      setPublicKey(data.public_key_pem);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="form-container">
      <h2>Retrieve Airplane Public Key</h2>

      <div className="form-group">
        <label>Airplane Name:</label>
        <input
          type="text"
          value={airplaneName}
          onChange={(e) => setAirplaneName(e.target.value)}
          placeholder="Enter airplane name"
        />
      </div>

      <button onClick={handleRetrieve}>Retrieve Public Key</button>

      {error && <p className="error">❌ {error}</p>}
      {publicKey && (
        <div className="key-display">
          <h3>Public Key:</h3>
          <pre>{publicKey}</pre>
        </div>
      )}
    </div>
  );
};

export default RetrieveAirplanePublicKey;