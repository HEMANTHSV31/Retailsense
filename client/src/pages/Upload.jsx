import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadService } from '../services/index';
import { LoadingSpinner, ErrorState } from '../components/common/LoadingState';
import {
  UploadCloud, CheckCircle2, AlertTriangle, FileText, Table2, HardDrive,
  XCircle, Loader2 as LoaderIcon, Zap, ArrowRight, TrendingUp, Trash2, FileSpreadsheet
} from 'lucide-react';

function StatusPill({ status }) {
  const styles = {
    cleaned: 'badge-ok',
    error: 'badge-critical',
    processing: 'badge-low',
    uploaded: 'badge-excess',
  };
  const icons = {
    cleaned: CheckCircle2,
    error: XCircle,
    processing: LoaderIcon,
    uploaded: UploadCloud,
  };
  const Icon = icons[status] || FileText;
  return (
    <span className={styles[status] || 'badge-neutral'}>
      <Icon className="w-3 h-3" />
      {status}
    </span>
  );
}

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const fetchHistory = () => {
    uploadService.history()
      .then(r => setHistory(r.data))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const res = await uploadService.upload(file);
      setResult(res.data);
      fetchHistory();
    } catch (e) {
      const errDetail = e.response?.data?.detail;
      if (typeof errDetail === 'string') {
        setError(errDetail);
      } else if (Array.isArray(errDetail)) {
        setError(errDetail.map(m => m.msg || JSON.stringify(m)).join('; '));
      } else if (typeof errDetail === 'object' && errDetail !== null) {
        setError(errDetail.msg || JSON.stringify(errDetail));
      } else {
        setError(e.message || 'Upload failed');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to remove all existing data in the tables? This will clear sales, inventory, and forecasts so you can insert fresh data.')) {
      return;
    }
    setResetting(true);
    setError(null);
    try {
      await uploadService.reset();
      setResult(null);
      setFile(null);
      fetchHistory();
      alert('All tables have been cleared. Ready for your fresh Excel/CSV data upload!');
    } catch (e) {
      setError(e.response?.data?.detail || 'Reset failed');
    } finally {
      setResetting(false);
    }
  };

  const isExcel = file?.name?.toLowerCase().endsWith('.xlsx') || file?.name?.toLowerCase().endsWith('.xls');

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Data Ingestion Engine</h1>
          <p className="page-subtitle">Upload retail sales in Excel (.xlsx) or CSV format — auto-validated, cleaned, and ingested into database</p>
        </div>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-700 bg-red-50 hover:bg-red-100 rounded-lg text-xs font-semibold transition-all self-start"
          title="Clear all sales, inventory, and forecast data"
        >
          {resetting ? (
            <>
              <LoaderIcon className="w-3.5 h-3.5 animate-spin" />
              <span>Clearing Tables...</span>
            </>
          ) : (
            <>
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear / Reset All Data</span>
            </>
          )}
        </button>
      </div>

      {/* Upload Zone */}
      <div className="content-section">
        <div className="content-section-title flex items-center justify-between">
          <span>Upload Excel (.xlsx) or CSV</span>
          <span className="text-xs font-normal text-neutral-500">Supports .xlsx, .xls, .csv</span>
        </div>
        <div className="border-2 border-dashed border-neutral-300 hover:border-neutral-800 rounded-xl p-10 text-center bg-neutral-50/50 hover:bg-neutral-100/50 transition-all group">
          <div className="w-14 h-14 rounded-2xl bg-neutral-900/10 text-neutral-900 flex items-center justify-center mx-auto mb-4 group-hover:scale-105 transition-transform">
            {isExcel ? (
              <FileSpreadsheet className="w-7 h-7 text-emerald-600" />
            ) : (
              <UploadCloud className="w-7 h-7" />
            )}
          </div>
          <p className="text-sm font-bold text-neutral-900 mb-2">
            Drop your Excel (.xlsx) or CSV file here, or click to browse
          </p>
          <p className="text-xs text-neutral-600 mb-5">
            Expected columns: <code className="bg-neutral-200 text-neutral-900 px-1.5 py-0.5 rounded text-xs">date, sales (or qty), item_id (or sku), store_id</code> · optional: <code className="bg-neutral-200 text-neutral-900 px-1.5 py-0.5 rounded text-xs">sell_price, category</code>
          </p>
          <div className="flex justify-center">
            <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-neutral-900 text-white text-sm font-medium cursor-pointer hover:bg-neutral-700 transition-colors shadow-sm">
              <UploadCloud className="w-4 h-4" />
              Choose Excel or CSV File
              <input
                type="file"
                accept=".xlsx,.xls,.csv,.txt"
                onChange={e => setFile(e.target.files[0])}
                className="sr-only"
              />
            </label>
          </div>
          {file && (
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-neutral-800 animate-fade-in font-medium">
              {isExcel ? (
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              ) : (
                <FileText className="w-4 h-4 text-blue-600" />
              )}
              <span>{file.name}</span>
              <span className="text-neutral-500 font-normal">· {(file.size / 1024).toFixed(1)} KB</span>
            </div>
          )}
          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-gradient mt-5 inline-flex items-center gap-2 px-6 py-2.5"
            >
              {uploading ? (
                <>
                  <LoaderIcon className="w-4 h-4 animate-spin text-white" />
                  <span>Processing & Ingesting...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  <span>Upload & Ingest to Database</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {/* Upload Result */}
      {result && (
        <div className={`content-section animate-fade-in ${result.errors?.length > 0 ? '!border-red-400' : '!border-emerald-500'}`}>
          <div className="flex items-center gap-2.5 mb-4">
            {result.errors?.length > 0 ? (
              <AlertTriangle className="w-5 h-5 text-red-600" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            )}
            <span className={`font-bold ${result.errors?.length > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
              {result.errors?.length > 0 ? 'Validation Failed' : 'Upload & Database Ingestion Successful'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-5">
            <div className="text-center p-4 bg-neutral-50 rounded-xl border border-neutral-200">
              <Table2 className="w-5 h-5 text-neutral-800 mx-auto mb-1.5" />
              <div className="text-2xl font-bold text-neutral-900 tabular-nums">{result.row_count?.toLocaleString()}</div>
              <div className="text-xs text-neutral-500 mt-0.5">Rows Ingested</div>
            </div>
            <div className="text-center p-4 bg-neutral-50 rounded-xl border border-neutral-200">
              <FileText className="w-5 h-5 text-emerald-600 mx-auto mb-1.5" />
              <div className="text-2xl font-bold text-neutral-900 tabular-nums">{result.column_count}</div>
              <div className="text-xs text-neutral-500 mt-0.5">Columns Detected</div>
            </div>
            <div className="text-center p-4 bg-neutral-50 rounded-xl border border-neutral-200">
              <HardDrive className="w-5 h-5 text-indigo-600 mx-auto mb-1.5" />
              <div className="text-2xl font-bold text-neutral-900 tabular-nums">{result.file_size_kb?.toFixed(1)} KB</div>
              <div className="text-xs text-neutral-500 mt-0.5">File Size</div>
            </div>
          </div>

          {result.warnings?.map((w, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50 border border-amber-200 p-3 rounded-lg mb-2 animate-fade-in">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-600" />
              <span>{w}</span>
            </div>
          ))}
          {result.errors?.map((e, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-red-800 bg-red-50 border border-red-200 p-3 rounded-lg mb-2 animate-fade-in">
              <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600" />
              <span>{e}</span>
            </div>
          ))}

          {result.errors?.length === 0 && (
            <div className="mt-5 p-5 bg-neutral-900 rounded-xl text-white shadow-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-widest">
                    <CheckCircle2 className="w-4 h-4" /> Data Ingested & Active in Database
                  </div>
                  <h3 className="text-base font-bold text-white mt-1">Ready for Decision Intelligence</h3>
                  <p className="text-xs text-neutral-300 mt-0.5">
                    Your new dataset is live. You can now run ML forecasts, calculate optimal inventory reorder points, or view decision intelligence actions.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate('/decisions')}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 text-xs font-bold rounded-lg transition-all shadow-sm"
                  >
                    <Zap className="w-3.5 h-3.5 fill-current" />
                    Decision Center
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => navigate('/forecast')}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-neutral-800 hover:bg-neutral-700 text-white text-xs font-semibold rounded-lg transition-all border border-neutral-700"
                  >
                    <TrendingUp className="w-3.5 h-3.5" />
                    Forecast
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upload History */}
      <div className="content-section">
        <div className="content-section-title">Upload History</div>
        {loadingHistory ? (
          <LoadingSpinner message="Loading history..." />
        ) : history && history.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Format</th>
                  <th className="text-right">Rows</th>
                  <th className="text-right">Size</th>
                  <th className="text-center">Status</th>
                  <th className="text-right">Uploaded At</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => {
                  const isXls = h.original_filename?.toLowerCase().endsWith('.xlsx') || h.original_filename?.toLowerCase().endsWith('.xls');
                  return (
                    <tr key={i} className="hover:bg-neutral-50/70 transition-colors">
                      <td className="font-semibold text-neutral-900">
                        <span className="inline-flex items-center gap-2">
                          {isXls ? (
                            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <FileText className="w-4 h-4 text-neutral-500" />
                          )}
                          {h.original_filename}
                        </span>
                      </td>
                      <td>
                        <span className="text-xs uppercase font-mono px-2 py-0.5 bg-neutral-100 rounded text-neutral-700">
                          {isXls ? 'Excel' : 'CSV'}
                        </span>
                      </td>
                      <td className="num font-semibold text-neutral-900">{h.row_count?.toLocaleString() || '—'}</td>
                      <td className="num text-neutral-700">{h.file_size_kb?.toFixed(1) || '—'} KB</td>
                      <td className="text-center"><StatusPill status={h.status} /></td>
                      <td className="num text-neutral-500">{new Date(h.created_at).toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-neutral-500 text-sm py-4">No uploads yet. Upload an Excel or CSV file above.</p>
        )}
      </div>
    </div>
  );
}
