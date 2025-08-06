import React, { useState } from 'react';
import '../App.css';

const StoreClientKey = () => {
  const [keyName, setKeyName] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (!keyName || !publicKey) {
      setError('Please provide both key name and public key.');
      return;
    }

    try {
      const res = await fetch('/store-client-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          key_name: keyName,
          public_key: publicKey,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to store public key.');
      }

      setMessage(data.message);
      setKeyName('');
      setPublicKey('');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="form-container">
      <h2>Store Client Public Key</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Key Name:</label>
          <input
            type="text"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            placeholder="e.g. client123"
          />
        </div>

        <div className="form-group">
          <label>Public Key (PEM):</label>
          <textarea
            rows="8"
            value={publicKey}
            onChange={(e) => setPublicKey(e.target.value)}
            placeholder="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
          />
        </div>

        <button type="submit">Save Client Key</button>
      </form>

      {message && <p className="success">✅ {message}</p>}
      {error && <p className="error">❌ {error}</p>}
    </div>
  );
};

export default StoreClientKey;