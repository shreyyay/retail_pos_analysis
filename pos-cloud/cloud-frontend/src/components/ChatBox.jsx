import React, { useState, useRef, useEffect } from 'react';
import { queryInsight } from '../services/api';

const EXAMPLES = [
  'What were my total sales this week?',
  'Which item sold the most last month?',
  'How much cash did I receive yesterday?',
  'Which customers have overdue Udhar?',
];

function ChatBox() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const ask = async (q) => {
    const text = (q || question).trim();
    if (!text) return;
    setQuestion('');
    setMessages(prev => [...prev, { role: 'user', text }]);
    setLoading(true);
    try {
      const res = await queryInsight(text);
      setMessages(prev => [...prev, { role: 'assistant', text: res.data.answer, rowCount: res.data.data?.length }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', text: e.response?.data?.detail || e.message }]);
    } finally { setLoading(false); }
  };

  return (
    <div>
      {messages.length === 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, color: '#888', marginBottom: 6 }}>Try asking:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {EXAMPLES.map(q => (
              <button key={q} onClick={() => ask(q)}
                style={{ padding: '5px 12px', background: '#f0f2f5', border: '1px solid #ddd', borderRadius: 20, fontSize: 12, cursor: 'pointer', color: '#444' }}>
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
      <div style={{ maxHeight: 320, overflowY: 'auto', marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 10 }}>
            <div style={{
              maxWidth: '80%', padding: '10px 14px', fontSize: 14, lineHeight: 1.5,
              borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              background: m.role === 'user' ? '#1e3a5f' : m.role === 'error' ? '#fff5f5' : '#f0f2f5',
              color: m.role === 'user' ? '#fff' : m.role === 'error' ? '#c0392b' : '#333',
            }}>
              {m.text}
              {m.rowCount > 0 && <div style={{ fontSize: 11, marginTop: 4, opacity: 0.7 }}>{m.rowCount} rows</div>}
            </div>
          </div>
        ))}
        {loading && <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 10 }}><div style={{ padding: '10px 14px', background: '#f0f2f5', borderRadius: '16px 16px 16px 4px', fontSize: 14, color: '#999' }}>Thinking…</div></div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input type="text" value={question} onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !loading && ask()} disabled={loading}
          placeholder="Ask about your store data…"
          style={{ flex: 1, padding: '10px 14px', border: '1px solid #ddd', borderRadius: 8, fontSize: 14 }} />
        <button onClick={() => ask()} disabled={loading || !question.trim()}
          style={{ padding: '10px 20px', background: '#1e3a5f', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, cursor: 'pointer', opacity: loading || !question.trim() ? 0.6 : 1 }}>
          Ask
        </button>
      </div>
    </div>
  );
}
export default ChatBox;
