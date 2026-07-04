'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Avatar } from '@/components/ui/Avatar';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Check, X, AlertTriangle, Clock, Loader2 } from 'lucide-react';
import { containerVariants, cardVariants } from '@/lib/animations';
import { useLeaveRequests, useApproveLeave, useCancelLeave, useDashboard } from '@/hooks/useApi';
import type { AdminDashboard } from '@/types';

export default function ApprovalsPage() {
  const [rejectComment, setRejectComment] = useState('');
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const { data: pendingData, isLoading } = useLeaveRequests({ status: 'pending', limit: 50 });
  const { data: dashData } = useDashboard();
  const approveMutation = useApproveLeave();
  const cancelMutation = useCancelLeave();

  const requests = pendingData?.items ?? [];
  const adminDash = dashData?.role === 'admin' ? (dashData.data as AdminDashboard) : null;

  const handleApprove = (leaveId: string) => {
    approveMutation.mutate({ leaveId, data: { status: 'approved' } });
  };

  const handleReject = (leaveId: string) => {
    cancelMutation.mutate(leaveId);
    setRejectingId(null);
    setRejectComment('');
  };

  const urgentCount = requests.filter(r => r.remarks?.toLowerCase().includes('urgent') || r.remarks?.toLowerCase().includes('emergency') || r.remarks?.toLowerCase().includes('sick') || r.remarks?.toLowerCase().includes('bereavement')).length;

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={cardVariants}>
          <div className="grid grid-cols-3 gap-4">
            <GlassCard className="p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-400 font-[family-name:var(--font-geist-mono)]">{requests.length}</p>
                  <p className="text-xs text-[var(--text-muted)]">Pending</p>
                </div>
              </div>
            </GlassCard>
            <GlassCard className="p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-red-400 font-[family-name:var(--font-geist-mono)]">{urgentCount}</p>
                  <p className="text-xs text-[var(--text-muted)]">Urgent</p>
                </div>
              </div>
            </GlassCard>
            <GlassCard className="p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Check className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-emerald-400 font-[family-name:var(--font-geist-mono)]">{adminDash?.pending_leaves?.length ?? '—'}</p>
                  <p className="text-xs text-[var(--text-muted)]">Recent pending</p>
                </div>
              </div>
            </GlassCard>
          </div>
        </motion.div>

        <motion.div variants={cardVariants}>
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-6">Pending Approvals</h3>

            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[var(--text-muted)] animate-spin" />
              </div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence>
                  {requests.map(req => {
                    const isUrgent = req.remarks?.toLowerCase().includes('urgent') || req.remarks?.toLowerCase().includes('emergency') || req.remarks?.toLowerCase().includes('sick') || req.remarks?.toLowerCase().includes('bereavement');
                    return (
                      <motion.div
                        key={req.id}
                        layout
                        exit={{ opacity: 0, x: -100 }}
                        transition={{ duration: 0.2 }}
                      >
                        <GlassCard hover className={`p-5 ${isUrgent ? 'border-l-4 border-l-red-500' : ''}`}>
                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div className="flex items-start gap-4">
                              <Avatar name={req.employee_name ?? 'Employee'} />
                              <div>
                                <div className="flex items-center gap-2">
                                  <h4 className="font-medium text-[var(--text-primary)]">{req.employee_name ?? 'Unknown'}</h4>
                                  <StatusBadge variant="info">{req.leave_type}</StatusBadge>
                                  {isUrgent && <StatusBadge variant="high" pulse>Urgent</StatusBadge>}
                                </div>
                                <p className="text-sm text-[var(--text-secondary)] mt-0.5">
                                  {req.start_date} – {req.end_date}
                                  {req.days ? ` (${req.days} days)` : ''}
                                </p>
                                {req.remarks && (
                                  <p className="text-xs text-[var(--text-muted)] mt-1 italic">&quot;{req.remarks}&quot;</p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 w-full sm:w-auto">
                              <Button
                                variant="success"
                                size="sm"
                                onClick={() => handleApprove(req.id)}
                                disabled={approveMutation.isPending}
                              >
                                {approveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Approve
                              </Button>
                              <Button variant="danger" size="sm" onClick={() => setRejectingId(req.id)}>
                                <X className="w-4 h-4" /> Reject
                              </Button>
                            </div>
                          </div>
                          {rejectingId === req.id && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              className="mt-4 pt-4 border-t border-white/[0.06] flex gap-2"
                            >
                              <input
                                value={rejectComment}
                                onChange={e => setRejectComment(e.target.value)}
                                className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded-xl px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-red-500"
                                placeholder="Reason for rejection..."
                              />
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => handleReject(req.id)}
                                disabled={cancelMutation.isPending}
                              >
                                {cancelMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Confirm'}
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => { setRejectingId(null); setRejectComment(''); }}>
                                Cancel
                              </Button>
                            </motion.div>
                          )}
                        </GlassCard>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
                {requests.length === 0 && (
                  <div className="text-center py-12">
                    <Check className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                    <p className="text-[var(--text-primary)] font-medium">All caught up!</p>
                    <p className="text-sm text-[var(--text-muted)]">No pending approvals</p>
                  </div>
                )}
              </div>
            )}
          </GlassCard>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
