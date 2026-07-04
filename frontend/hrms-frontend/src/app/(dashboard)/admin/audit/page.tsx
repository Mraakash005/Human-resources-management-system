'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Download, Search, Calendar, User, FileText, DollarSign, Shield, Clock, Loader2, AlertCircle } from 'lucide-react';
import { containerVariants, cardVariants } from '@/lib/animations';
import { useDashboard } from '@/hooks/useApi';
import type { DashboardRecentActivity } from '@/types';

const actionIcons: Record<string, { icon: React.ElementType; color: string }> = {
  leave_approved: { icon: Calendar, color: 'text-amber-400' },
  leave_rejected: { icon: Calendar, color: 'text-red-400' },
  leave_requested: { icon: Calendar, color: 'text-cyan-400' },
  payroll_generated: { icon: DollarSign, color: 'text-emerald-400' },
  profile_updated: { icon: User, color: 'text-blue-400' },
  employee_created: { icon: User, color: 'text-emerald-400' },
  employee_deactivated: { icon: User, color: 'text-red-400' },
  check_in: { icon: Clock, color: 'text-emerald-400' },
  security_event: { icon: Shield, color: 'text-red-400' },
};

function matchAction(activity: DashboardRecentActivity): string {
  const a = activity.action.toLowerCase();
  if (a.includes('approved')) return 'leave_approved';
  if (a.includes('rejected') || a.includes('denied')) return 'leave_rejected';
  if (a.includes('leave') && a.includes('request')) return 'leave_requested';
  if (a.includes('payroll')) return 'payroll_generated';
  if (a.includes('profile') || a.includes('updated')) return 'profile_updated';
  if (a.includes('created') || a.includes('onboard')) return 'employee_created';
  if (a.includes('deactivat') || a.includes('terminated')) return 'employee_deactivated';
  if (a.includes('check_in') || a.includes('check-in') || a.includes('checkin')) return 'check_in';
  if (a.includes('security') || a.includes('login')) return 'security_event';
  return 'default';
}

export default function AuditPage() {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');

  const { data: dashData, isLoading } = useDashboard();

  const adminDash = dashData?.role === 'admin' ? dashData.data : null;
  const recentActivity = adminDash?.recent_activity ?? [];

  const filtered = recentActivity.filter(entry => {
    const matchFilter = filter === 'all' || matchAction(entry).includes(filter);
    const matchSearch = entry.description.toLowerCase().includes(search.toLowerCase()) || entry.action.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={cardVariants}>
          <GlassCard className="p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Audit Log</h3>
              <Button variant="secondary" size="sm"><Download className="w-4 h-4" /> Export CSV</Button>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                  placeholder="Search activity..."
                />
              </div>
              <select
                value={filter}
                onChange={e => setFilter(e.target.value)}
                className="bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
              >
                <option value="all">All Actions</option>
                <option value="leave">Leave Actions</option>
                <option value="payroll">Payroll Actions</option>
                <option value="profile">Profile Changes</option>
                <option value="security">Security Events</option>
              </select>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[var(--text-muted)] animate-spin" />
              </div>
            ) : recentActivity.length === 0 ? (
              <div className="text-center py-16">
                <AlertCircle className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3" />
                <p className="text-[var(--text-primary)] font-medium">Audit Log Coming Soon</p>
                <p className="text-sm text-[var(--text-muted)] mt-1">A dedicated audit log endpoint is under development.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filtered.map((entry, idx) => {
                  const actionKey = matchAction(entry);
                  const iconData = actionIcons[actionKey] || { icon: FileText, color: 'text-[var(--text-muted)]' };
                  const Icon = iconData.icon;
                  return (
                    <div key={idx} className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/[0.02] transition-colors">
                      <div className={`w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center flex-shrink-0 ${iconData.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">{entry.action}</span>
                        </div>
                        <p className="text-xs text-[var(--text-muted)] truncate">{entry.description}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs text-[var(--text-muted)]">
                          {entry.timestamp ? new Date(entry.timestamp).toLocaleString('en-US', {
                            month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true,
                          }) : '—'}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {filtered.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-[var(--text-muted)]">No matching activity found.</p>
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
