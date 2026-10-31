import { useState, useRef, useEffect } from 'react';
import { advisorService } from '../services';
import { Send, Bot, Sparkles, AlertCircle } from 'lucide-react';

const SUGGESTIONS = [
  'Why did sales decline?',
  'Which products should I reorder?',
  'Which stores are underperforming?',
  'What products are likely to see increased demand?',
  'What should I do next?',
];

function formatInlineText(text) {
  if (!text) return null;
  // Replace &bull; with bullet character
  const clean = text.replace(/&bull;/g, '•');
  // Split on bold markdown **text**
  const parts = clean.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="font-semibold text-stone-950">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

function FormattedAdvisorMessage({ content }) {
  if (!content) return null;

  // Split into paragraphs / blocks
  const blocks = content.split(/\n\s*\n/);

  return (
    <div className="space-y-3 text-stone-800">
      {blocks.map((block, bIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Check if markdown table
        const lines = trimmed.split('\n').map((l) => l.trim());
        if (lines.length >= 2 && lines[0].startsWith('|') && lines[0].endsWith('|')) {
          const headerCells = lines[0].split('|').slice(1, -1).map((c) => c.trim());
          const rowLines = lines.slice(1).filter((l) => l.replace(/[|:\s-]/g, '').length > 0);
          return (
            <div key={bIdx} className="overflow-x-auto my-3 rounded-xl border border-stone-200 shadow-sm bg-white">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-stone-50 border-b border-stone-200">
                    {headerCells.map((h, i) => (
                      <th key={i} className="px-3.5 py-2.5 font-bold text-stone-800">
                        {formatInlineText(h)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {rowLines.map((rowStr, rIdx) => {
                    const cells = rowStr.split('|').slice(1, -1).map((c) => c.trim());
                    return (
                      <tr key={rIdx} className="hover:bg-stone-50/60 transition-colors">
                        {cells.map((cell, cIdx) => (
                          <td key={cIdx} className="px-3.5 py-2 text-stone-700">
                            {formatInlineText(cell)}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        }

        // Check if Heading (e.g. ### Title or ## Title)
        if (trimmed.startsWith('#')) {
          const title = trimmed.replace(/^#+\s*/, '');
          return (
            <div key={bIdx} className="pt-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-100 pb-1 flex items-center gap-1.5">
                {formatInlineText(title)}
              </h3>
            </div>
          );
        }

        // Check if list of bullet items
        const isBulletList = lines.every((l) => l.startsWith('- ') || l.startsWith('* ') || l.match(/^\d+\.\s/));
        if (isBulletList) {
          return (
            <ul key={bIdx} className="space-y-1.5 pl-1 my-2">
              {lines.map((line, lIdx) => {
                const bulletText = line.replace(/^[-*]\s+|\d+\.\s+/, '');
                return (
                  <li key={lIdx} className="flex items-start gap-2.5 text-xs text-stone-700 leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-stone-400 mt-1.5 flex-shrink-0" />
                    <span className="flex-1">{formatInlineText(bulletText)}</span>
                  </li>
                );
              })}
            </ul>
          );
        }

        // Regular paragraph with potential bullets mixed in
        const paragraphLines = trimmed.split('\n');
        return (
          <div key={bIdx} className="space-y-1.5 text-xs leading-relaxed text-stone-700">
            {paragraphLines.map((line, pIdx) => {
              if (line.startsWith('- ') || line.startsWith('* ')) {
                return (
                  <div key={pIdx} className="flex items-start gap-2.5 pl-1 py-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-stone-400 mt-1.5 flex-shrink-0" />
                    <span className="flex-1">{formatInlineText(line.slice(2))}</span>
                  </div>
                );
              }
              return (
                <p key={pIdx} className="text-xs text-stone-700 leading-relaxed">
                  {formatInlineText(line)}
                </p>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export default function Advisor() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const ask = async (question) => {
    if (!question.trim() || loading) return;
    setError(null);
    setMessages((m) => [...m, { role: 'user', content: question }]);
    setInput('');
    setLoading(true);
    try {
      const history = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
      const res = await advisorService.ask(question, history);
      setMessages((m) => [...m, {
        role: 'assistant',
        content: res.data.answer,
        mode: res.data.mode,
      }]);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to get an answer. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6 animate-fade-in">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-stone-900 text-white flex items-center justify-center shadow-sm">
            <Bot size={22} />
          </div>
          <div>
            <h1 className="page-title text-xl font-bold text-stone-900">AI Business Advisor</h1>
            <p className="page-subtitle text-xs text-stone-500">
              Grounded in multi-store sales, ML demand forecasts, and autonomous supply chain signals.
            </p>
          </div>
        </div>
      </div>

      {messages.length === 0 && !loading && (
        <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm space-y-3">
          <p className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
            Suggested Strategic Queries:
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium bg-stone-50 border-stone-200 text-stone-700 hover:bg-stone-900 hover:text-white transition-all shadow-2xs"
              >
                <Sparkles size={12} className="text-purple-600" />
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-5 py-4 text-xs leading-relaxed ${
              m.role === 'user'
                ? 'bg-stone-900 text-white shadow-sm'
                : 'bg-white border border-stone-200 text-stone-800 shadow-sm'
            }`}>
              {m.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-stone-100">
                  <div className="w-5 h-5 rounded-md bg-stone-100 flex items-center justify-center text-stone-700">
                    <Bot size={13} />
                  </div>
                  <span className="text-xs font-bold text-stone-900">RetailIQ Intelligence</span>
                  {m.mode?.includes('groq') ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-full ml-auto">
                      <Sparkles size={10} /> Groq LLaMA AI
                    </span>
                  ) : m.mode === 'rules' ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full ml-auto">
                      <Sparkles size={10} /> Rules Engine
                    </span>
                  ) : null}
                </div>
              )}
              {m.role === 'user' ? (
                <div className="text-xs leading-relaxed">{m.content}</div>
              ) : (
                <FormattedAdvisorMessage content={m.content} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-stone-200 rounded-2xl px-4 py-3 text-xs text-stone-600 flex items-center gap-2.5 shadow-sm">
              <div className="animate-spin h-3.5 w-3.5 border-2 border-stone-900 border-t-transparent rounded-full" />
              Synthesizing multi-store data and evaluating trade-offs...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="flex items-center gap-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      <form
        onSubmit={(e) => { e.preventDefault(); ask(input); }}
        className="flex gap-2 rounded-2xl border p-2 sm:p-2.5 bg-white shadow-sm sticky bottom-4 border-stone-200"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about sales, replenishment, forecasts, stores, or profit trade-offs..."
          className="flex-1 bg-transparent px-3 py-2 text-xs outline-none text-stone-900 placeholder:text-stone-400"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl px-4 py-2 flex items-center gap-1.5 bg-stone-900 text-white text-xs font-semibold hover:bg-stone-800 disabled:opacity-50 transition-all shadow-sm"
        >
          <Send size={14} /> Ask Advisor
        </button>
      </form>
    </div>
  );
}
