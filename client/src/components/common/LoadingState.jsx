import { AlertTriangle, Inbox, Loader2 } from 'lucide-react';

export function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-400">
      <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-3" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function ErrorState({ message = 'Something went wrong', onRetry }) {
  let displayMessage = 'An unexpected error occurred';
  if (typeof message === 'string') {
    displayMessage = message;
  } else if (Array.isArray(message)) {
    displayMessage = message.map(m => m.msg || (typeof m === 'object' ? JSON.stringify(m) : String(m))).join('; ');
  } else if (typeof message === 'object' && message !== null) {
    displayMessage = message.msg || message.detail || JSON.stringify(message);
  } else {
    displayMessage = String(message || 'An error occurred');
  }

  return (
    <div className="card p-8 flex flex-col items-center justify-center text-center">
      <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-3">
        <AlertTriangle className="w-6 h-6 text-red-500" />
      </div>
      <p className="text-sm font-semibold text-red-600 mb-1">Notice</p>
      <p className="text-sm text-neutral-600 mb-5 max-w-md">{displayMessage}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary">Try Again</button>
      )}
    </div>
  );
}

export function EmptyState({ message = 'No data available', icon: Icon = Inbox }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-slate-400">
      <div className="w-12 h-12 rounded-full bg-slate-800/60 flex items-center justify-center mb-3">
        <Icon className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-sm">{message}</p>
    </div>
  );
}


