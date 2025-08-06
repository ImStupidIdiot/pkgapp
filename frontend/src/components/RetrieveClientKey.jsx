import React, { useState } from 'react';
import '../App.css';

const RetrieveClientKey = () => {
  const [name, setName] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const retrieveKey = async () => {
    setError('');
    setPublicKey('');

    if (!name.trim()) {
      setError('Please enter a client name.');
      return;
    }
  

    setLoading(true);
    try {
      const response = await fetch(`/retrieve-key/client/${encodeURIComponent(name)}`);

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to retrieve key');
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
      <h2>Retrieve Client Public Key</h2>
      <input
        type="text"
        placeholder="Enter client name (e.g. CompanyA)."
        value={name}
        onChange={e => setName(e.target.value)}
      />
      <button onClick={retrieveKey} disabled={loading}>
        {loading ? 'Retrieving...' : 'Retrieve Key'}
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

export default RetrieveClientKey;