import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function SharedWithMeError({ onRetry }) {
  return (
    <div className="shared-error">
      <span><AlertTriangle size={24} /></span>
      <h2>We couldn't load your shared files</h2>
      <p>Check your connection and try again.</p>
      <button className="btn btn-primary" onClick={onRetry}><RefreshCw size={15} /> Try again</button>
    </div>
  );
}
