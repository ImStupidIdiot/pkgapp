import React, { useState } from 'react';
import '../App.css';

const ClientKeyGenerator = () => {
  const [name, setName] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateKey = async () => {
    setError('');
    setPublicKey('');

    if (!name.trim()) {
      setError('Please enter a key name.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/generate-key/client', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to generate key');
      }

      const data = await response.json();
      setPublicKey(data.public_key_pem);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Generate Named Client Key</h2>
      <div>(Spaces will be ignored)</div>
      <input
        type="text"
        placeholder="Enter key name (e.g. CompanyA)."
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button onClick={generateKey} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Key'}
      </button>

      {publicKey && (
        <>
          <h4>Public Key for "{name}":</h4>
          <textarea
            rows={10}
            readOnly
            value={publicKey}
          />
        </>
      )}

      {error && <p className="error-message">❌ {error}</p>}
    </div>
  );
};

export default ClientKeyGenerator;