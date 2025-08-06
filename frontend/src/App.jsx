import React from 'react';
import ClientKeyGenerator from './components/ClientKeyGenerator';
import RetrieveClientKey from './components/RetrieveClientKey';
import EncryptSoftwareUploader from './components/EncryptSoftwareUploader';
import SaveAirplaneKey from './components/SaveAirplaneKey';
import AirplaneKeyGenerator from './components/AirplaneKeyGenerator';
import RetrieveAirplanePublicKey from './components/RetrieveAirplanePublicKey';
import StoreClientKey from './components/StoreClientKey';
import DecryptPackageUploader from './components/DecryptPackageUploader';

function App() {
  return (
    <div className="App">
      <h1>Aircraft Software Tool</h1>
      <h2> Sender Side </h2>
      <ClientKeyGenerator />
      <RetrieveClientKey />
      <EncryptSoftwareUploader />
      <SaveAirplaneKey />
      <h2> Reciever Side </h2>
      <AirplaneKeyGenerator />
      <RetrieveAirplanePublicKey />
      <StoreClientKey />
      <DecryptPackageUploader />
    </div>
  );
}

export default App;