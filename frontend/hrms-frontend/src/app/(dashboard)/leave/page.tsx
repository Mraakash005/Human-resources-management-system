'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import {
  useLeaveRequests,
  useLeaveBalance,
  useCreateLeave,
  useCancelLeave,
  useLeaveAdvisor,
  useConversationalLeave,
  useGenerateLeaveEmail,
} from '@/hooks/useApi';
import {
  FileText, MessageSquare, Mic, Sparkles, Send, Calendar,
  ChevronRight, ChevronLeft, Loader2,
  AlertTriangle, CheckCircle2, XCircle, RefreshCw, Bot,
} from 'lucide-react';
import { containerVariants, cardVariants } from '@/lib/animations';

const tabs = [
  { id: 'apply', label: 'Apply Leave', icon: FileText },
  { id: 'requests', label: 'My Requests', icon: Calendar },
  { id: 'ai-doc', label: 'AI Documenter', icon: Sparkles },
  { id: 'voice', label: 'Voice-to-Leave', icon: Mic },
  { id: 'conversational', label: 'Conversational', icon: MessageSquare },
];

const LEAVE_TYPES = [
  { value: 'paid', label: 'Paid Leave' },
  { value: 'sick', label: 'Sick Leave' },
  { value: 'unpaid', label: 'Unpaid Leave' },
  { value: 'bereavement', label: 'Bereavement' },
  { value: 'medical', label: 'Medical' },
];

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function ApplyLeaveTab() {
  const [leaveType, setLeaveType] = useState('paid');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [remarks, setRemarks] = useState('');
  const [formalReason, setFormalReason] = useState('');
  const [sendEmail, setSendEmail] = useState(false);
  const [success, setSuccess] = useState(false);

  const createLeave = useCreateLeave();
  const { data: balanceData } = useLeaveBalance();

  const balances = balanceData?.data?.balances ?? [];
  const currentBalance = balances.find(b => b.leave_type === leaveType);

  const handleSubmit = () => {
    if (!startDate || !endDate || !remarks.trim()) return;
    createLeave.mutate(
      {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        remarks: remarks || undefined,
        formal_reason: formalReason || undefined,
        send_email: sendEmail,
      },
      {
        onSuccess: () => {
          setSuccess(true);
          setTimeout(() => setSuccess(false), 3000);
          setStartDate('');
          setEndDate('');
          setRemarks('');
          setFormalReason('');
        },
      },
    );
  };

  return (
    <GlassCard className="p-6">
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-6">Apply for Leave</h3>

      {currentBalance && (
        <div className="mb-6 p-4 bg-white/[0.03] rounded-xl border border-white/[0.06]">
          <p className="text-xs text-[var(--text-muted)] mb-1">Remaining Balance — {LEAVE_TYPES.find(t => t.value === leaveType)?.label}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-[var(--text-primary)]">{currentBalance.remaining}</span>
            <span className="text-sm text-[var(--text-muted)]">/ {currentBalance.total} days</span>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="text-xs text-[var(--text-secondary)] mb-1 block">Leave Type</label>
          <select
            value={leaveType}
            onChange={e => setLeaveType(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] focus:ring-2 focus:ring-[var(--accent-primary-glow)]"
          >
            {LEAVE_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-[var(--text-secondary)] mb-1 block">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
          </div>
          <div>
            <label className="text-xs text-[var(--text-secondary)] mb-1 block">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-[var(--text-secondary)] mb-1 block">Reason</label>
          <textarea
            rows={3}
            value={remarks}
            onChange={e => setRemarks(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] resize-none"
            placeholder="Describe your reason..."
          />
        </div>
        <div>
          <label className="text-xs text-[var(--text-secondary)] mb-1 block">Formal Reason (optional)</label>
          <input
            type="text"
            value={formalReason}
            onChange={e => setFormalReason(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            placeholder="Formal justification for the leave..."
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
          <input
            type="checkbox"
            checked={sendEmail}
            onChange={e => setSendEmail(e.target.checked)}
            className="rounded border-white/[0.15] bg-white/[0.05]"
          />
          Send email notification to HR
        </label>
        {createLeave.isError && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-400">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            {(createLeave.error as Error)?.message || 'Failed to submit leave request'}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-sm text-emerald-400">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            Leave request submitted successfully!
          </div>
        )}
        <Button
          onClick={handleSubmit}
          disabled={createLeave.isPending || !startDate || !endDate || !remarks.trim()}
          className="w-full"
        >
          {createLeave.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Submitting...</>
          ) : (
            'Submit Leave Request'
          )}
        </Button>
      </div>
    </GlassCard>
  );
}

function MyRequestsTab() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const limit = 10;

  const { data, isLoading, isError, refetch } = useLeaveRequests({
    page,
    limit,
    status: statusFilter || undefined,
  });
  const cancelLeave = useCancelLeave();

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / limit);

  const borderClass = (status: string) => {
    switch (status) {
      case 'pending': return 'border-l-amber-500';
      case 'approved': return 'border-l-emerald-500';
      case 'rejected': return 'border-l-red-500';
      case 'cancelled': return 'border-l-white/20';
      default: return 'border-l-white/20';
    }
  };

  const badgeVariant = (status: string): 'approved' | 'pending' | 'rejected' | 'info' => {
    switch (status) {
      case 'approved': return 'approved';
      case 'pending': return 'pending';
      case 'rejected': return 'rejected';
      case 'cancelled': return 'info';
      default: return 'info';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {['', 'pending', 'approved', 'rejected', 'cancelled'].map(s => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-[var(--accent-primary)] text-white'
                  : 'bg-white/[0.05] text-[var(--text-secondary)] hover:bg-white/[0.08]'
              }`}
            >
              {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <Button variant="secondary" onClick={() => refetch()}>
          <RefreshCw className="w-3 h-3" />
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
        </div>
      ) : isError ? (
        <div className="text-center py-12">
          <XCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-[var(--text-secondary)]">Failed to load leave requests</p>
          <Button variant="secondary" onClick={() => refetch()} className="mt-3">
            <RefreshCw className="w-3 h-3" /> Retry
          </Button>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-sm text-[var(--text-muted)]">
          <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
          No leave requests found
        </div>
      ) : (
        <>
          {items.map((req) => (
            <GlassCard key={req.id} hover className={`p-5 border-l-4 ${borderClass(req.status)}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-[var(--text-primary)]">
                    {LEAVE_TYPES.find(t => t.value === req.leave_type)?.label || req.leave_type}
                  </h4>
                  <p className="text-sm text-[var(--text-secondary)] mt-0.5">
                    {formatDate(req.start_date)} — {formatDate(req.end_date)}
                    {req.days && <span className="text-[var(--text-muted)]"> ({req.days} day{req.days !== 1 ? 's' : ''})</span>}
                  </p>
                  {req.remarks && (
                    <p className="text-xs text-[var(--text-muted)] mt-1 italic">&quot;{req.remarks}&quot;</p>
                  )}
                  {req.admin_comment && (
                    <p className="text-xs text-[var(--text-muted)] mt-1 italic">
                      Admin: &quot;{req.admin_comment}&quot;
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-3">
                  <StatusBadge variant={badgeVariant(req.status)}>{req.status}</StatusBadge>
                  {req.status === 'pending' && (
                    <button
                      onClick={() => cancelLeave.mutate(req.id)}
                      disabled={cancelLeave.isPending}
                      className="text-xs text-red-400 hover:text-red-300 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </GlassCard>
          ))}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.08] disabled:opacity-30 transition-all"
              >
                <ChevronLeft className="w-4 h-4 text-[var(--text-primary)]" />
              </button>
              <span className="text-sm text-[var(--text-secondary)]">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.08] disabled:opacity-30 transition-all"
              >
                <ChevronRight className="w-4 h-4 text-[var(--text-primary)]" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AIDocTab() {
  const [informalReason, setInformalReason] = useState('');
  const [leaveType, setLeaveType] = useState('medical');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [employeeName, setEmployeeName] = useState('');

  const generateEmail = useGenerateLeaveEmail();

  const handleGenerate = () => {
    if (!informalReason.trim() || !startDate || !endDate || !employeeName.trim()) return;
    generateEmail.mutate({
      name: employeeName,
      leave_type: leaveType,
      start_date: startDate,
      end_date: endDate,
      reason: informalReason,
    });
  };

  const generatedEmail = generateEmail.data?.email;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <GlassCard className="p-6">
        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Informal Reason</h3>
        <div className="space-y-3">
          <input
            type="text"
            value={employeeName}
            onChange={e => setEmployeeName(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            placeholder="Your name..."
          />
          <select
            value={leaveType}
            onChange={e => setLeaveType(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
          >
            {LEAVE_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
          </div>
          <textarea
            rows={4}
            value={informalReason}
            onChange={e => setInformalReason(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] resize-none"
            placeholder="I have a fever and need rest..."
          />
        </div>
        <Button
          onClick={handleGenerate}
          className="w-full mt-4"
          disabled={generateEmail.isPending || !informalReason.trim() || !startDate || !endDate || !employeeName.trim()}
        >
          {generateEmail.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
          ) : (
            <><Sparkles className="w-4 h-4" /> Generate Email</>
          )}
        </Button>
        {generateEmail.isError && (
          <p className="text-xs text-red-400 mt-2">Failed to generate email. Please try again.</p>
        )}
      </GlassCard>

      <GlassCard className="p-6 border-cyan-500/20 relative overflow-hidden">
        <span className="absolute top-3 right-3 text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-2 py-0.5">AI</span>
        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Generated Email Preview</h3>
        {generateEmail.isPending ? (
          <div className="flex items-center justify-center h-40 text-sm text-[var(--text-muted)]">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              <span className="ml-2">AI is drafting...</span>
            </div>
          </div>
        ) : generatedEmail ? (
          <div className="bg-white/[0.02] rounded-xl p-4 text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
            {generatedEmail}
          </div>
        ) : (
          <div className="flex items-center justify-center h-40 text-sm text-[var(--text-muted)]">
            Click &quot;Generate Email&quot; to preview
          </div>
        )}
        {generatedEmail && (
          <div className="flex gap-2 mt-4">
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => {
                navigator.clipboard.writeText(generatedEmail);
              }}
            >
              Copy
            </Button>
            <Button className="flex-1">
              <Send className="w-4 h-4" /> Send to HR
            </Button>
          </div>
        )}
      </GlassCard>
    </div>
  );
}

function VoiceTab() {
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [supported, setSupported] = useState(true);

  const startRecording = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      setSupported(false);
      return;
    }
    const SpeechRecognitionClass = (window as Record<string, unknown>)['SpeechRecognition'] || (window as Record<string, unknown>)['webkitSpeechRecognition'];
    if (!SpeechRecognitionClass || typeof SpeechRecognitionClass !== 'function') {
      setSupported(false);
      return;
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition = new (SpeechRecognitionClass as any)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      setTranscript(event.results[0][0].transcript);
      setRecording(false);
    };
    recognition.onerror = () => setRecording(false);
    recognition.onend = () => setRecording(false);
    recognition.start();
    setRecording(true);
  };

  return (
    <GlassCard className="p-6">
      <div className="flex flex-col items-center py-8">
        {!supported ? (
          <div className="text-center">
            <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
            <p className="text-sm text-[var(--text-secondary)]">Speech recognition is not supported in this browser.</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">Try Chrome or Edge for voice input.</p>
          </div>
        ) : (
          <>
            <button
              onClick={() => recording ? setRecording(false) : startRecording()}
              className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                recording
                  ? 'bg-red-500/20 border-2 border-red-500 animate-pulse'
                  : 'bg-[var(--accent-primary)]/20 border-2 border-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/30'
              }`}
            >
              <Mic className={`w-10 h-10 ${recording ? 'text-red-400' : 'text-[var(--accent-primary)]'}`} />
            </button>
            <p className="text-sm text-[var(--text-secondary)] mt-4">
              {recording ? 'Recording... Click to stop' : 'Click to start recording'}
            </p>
            <div className="flex items-end gap-1 h-12 mt-4">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={`wave-${i}`}
                  className={`w-1 rounded-full transition-all duration-150 ${
                    recording ? 'bg-red-400 animate-pulse' : 'bg-white/[0.1]'
                  }`}
                  style={{
                    height: recording ? `${(Math.sin(i * 0.5) * 0.5 + 0.5) * 40 + 8}px` : '4px',
                    animationDelay: `${i * 50}ms`,
                  }}
                />
              ))}
            </div>
          </>
        )}

        {transcript && (
          <div className="mt-6 w-full max-w-md">
            <GlassCard className="p-4 border-cyan-500/20">
              <p className="text-xs text-[var(--text-muted)] mb-1">Transcription</p>
              <p className="text-sm text-[var(--text-secondary)] italic">{transcript}</p>
              <div className="mt-3 pt-3 border-t border-white/[0.06]">
                <Button variant="secondary" className="w-full" onClick={() => {}}>
                  Submit as Leave Request
                </Button>
              </div>
            </GlassCard>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

function ConversationalTab() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([
    { role: 'assistant', content: "Hi! Tell me about the leave you need — I'll take care of the rest." },
  ]);

  const conversationalLeave = useConversationalLeave();

  const send = () => {
    if (!input.trim() || conversationalLeave.isPending) return;
    const userMsg = input.trim();
    const newMessages = [...messages, { role: 'user' as const, content: userMsg }];
    setMessages(newMessages);
    setInput('');

    conversationalLeave.mutate(
      {
        message: userMsg,
        history: messages.map(m => ({ role: m.role, content: m.content })),
      },
      {
        onSuccess: (data) => {
          setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
        },
        onError: () => {
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: 'Sorry, I encountered an error processing your request. Please try again.',
          }]);
        },
      },
    );
  };

  return (
    <GlassCard className="p-0 overflow-hidden">
      <div className="h-[400px] flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg, i) => (
            <div
              key={`msg-${i}-${msg.role}`}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center mr-2 mt-1 shrink-0">
                  <Bot className="w-3 h-3 text-cyan-400" />
                </div>
              )}
              <div
                className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm ${
                  msg.role === 'user'
                    ? 'bg-[var(--accent-primary)] text-white rounded-br-md'
                    : 'bg-white/[0.06] text-[var(--text-primary)] border border-white/[0.08] rounded-bl-md'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {conversationalLeave.isPending && (
            <div className="flex justify-start">
              <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center mr-2 mt-1 shrink-0">
                <Bot className="w-3 h-3 text-cyan-400" />
              </div>
              <div className="bg-white/[0.06] border border-white/[0.08] px-4 py-2.5 rounded-2xl rounded-bl-md">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="border-t border-white/[0.06] p-3 flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            placeholder="Tell me about your leave..."
            disabled={conversationalLeave.isPending}
          />
          <Button onClick={send} disabled={conversationalLeave.isPending || !input.trim()}>
            {conversationalLeave.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </GlassCard>
  );
}

export default function LeavePage() {
  const [activeTab, setActiveTab] = useState('apply');
  const { data: advisorData } = useLeaveAdvisor();
  const advisorTips = advisorData?.data ?? [];

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={cardVariants}>
          <div className="flex gap-1 p-1 bg-white/[0.03] rounded-2xl border border-white/[0.06] overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-[var(--accent-primary)] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.05]'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </motion.div>

        {advisorTips.length > 0 && activeTab === 'apply' && (
          <motion.div variants={cardVariants}>
            <GlassCard className="p-4 border-cyan-500/20">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-medium text-cyan-400">AI Advisor Tips</span>
              </div>
              <div className="space-y-2">
                {advisorTips.map((tip, i) => (
                  <div key={`tip-${i}-${tip.title}`} className="flex items-start gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                      tip.priority === 'high' ? 'bg-red-400' : tip.priority === 'medium' ? 'bg-amber-400' : 'bg-emerald-400'
                    }`} />
                    <p className="text-xs text-[var(--text-secondary)]">
                      <span className="font-medium text-[var(--text-primary)]">{tip.title}:</span> {tip.message}
                    </p>
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        )}

        <motion.div variants={cardVariants}>
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'apply' && <ApplyLeaveTab />}
              {activeTab === 'requests' && <MyRequestsTab />}
              {activeTab === 'ai-doc' && <AIDocTab />}
              {activeTab === 'voice' && <VoiceTab />}
              {activeTab === 'conversational' && <ConversationalTab />}
            </motion.div>
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
