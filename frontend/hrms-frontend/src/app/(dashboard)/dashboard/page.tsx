'use client';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import {
  LogIn, LogOut, Calendar, Sparkles,
  ChevronRight, Clock,
  Users, AlertTriangle, CheckCircle
} from 'lucide-react';
import { useUser } from '@clerk/nextjs';
import { useDashboard, useCheckin, useCheckout, useNudges, useTodayAttendance } from '@/hooks/useApi';
import { getGreeting, getCurrentDate, getDayOfWeek } from '@/lib/utils';
import { containerVariants, cardVariants } from '@/lib/animations';
import type { EmployeeDashboard, AdminDashboard } from '@/types';

function DashboardLoading() {
  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show">
      <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 [&>*]:break-inside-avoid [&>*]:mb-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <motion.div key={i} variants={cardVariants}>
            <Skeleton className="h-40 rounded-2xl" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

function EmployeeDashboardView({ data }: { data: EmployeeDashboard }) {
  const { user } = useUser();
  const { data: todayData } = useTodayAttendance();
  const userName = user?.firstName ? `${user.firstName} ${user.lastName || ''}`.trim() : 'Employee';
  const attendance = data.attendance;
  const today = todayData?.data;
  const leaveBalance = data.leave_balance;

  return (
    <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 [&>*]:break-inside-avoid [&>*]:mb-6">
      {/* Welcome Banner */}
      <motion.div variants={cardVariants} className="sm:col-span-2 lg:col-span-3">
        <GlassCard className="p-6 sm:p-8" glow="primary">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)]">
                {getGreeting()}, {userName}
              </h2>
              <p className="text-[var(--text-secondary)] mt-1">
                {getCurrentDate()} · {getDayOfWeek()}
              </p>
              <div className="flex items-center gap-2 mt-3">
                {attendance.status !== 'not_checked_in' ? (
                  <StatusBadge variant="present" pulse>
                    Checked in {attendance.check_in ? `at ${new Date(attendance.check_in).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}` : ''}
                  </StatusBadge>
                ) : (
                  <StatusBadge variant="absent">Not checked in</StatusBadge>
                )}
              </div>
            </div>
            {today?.can_check_in && <CheckInButton />}
            {today?.can_check_out && <CheckOutButton />}
          </div>
        </GlassCard>
      </motion.div>

      {/* Attendance Summary */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Attendance</h3>
            <Calendar className="w-4 h-4 text-[var(--accent-primary)]" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Status</span>
              <StatusBadge variant={attendance.status === 'present' ? 'present' : attendance.status === 'absent' ? 'absent' : 'info'}>
                {attendance.status}
              </StatusBadge>
            </div>
            {attendance.check_in && (
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Check In</span>
                <span className="text-[var(--text-primary)]">{new Date(attendance.check_in).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            )}
            {attendance.check_out && (
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Check Out</span>
                <span className="text-[var(--text-primary)]">{new Date(attendance.check_out).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            )}
            {attendance.duration_hours != null && (
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Hours</span>
                <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{attendance.duration_hours}h</span>
              </div>
            )}
          </div>
          <a href="/attendance" className="text-xs text-[var(--accent-primary)] hover:text-indigo-400 flex items-center gap-1 mt-3">
            View Calendar <ChevronRight className="w-3 h-3" />
          </a>
        </GlassCard>
      </motion.div>

      {/* Leave Balance */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Leave Balance</h3>
            <a href="/leave" className="text-xs text-[var(--accent-primary)] hover:text-indigo-400">Apply</a>
          </div>
          <div className="space-y-4">
            {[
              { key: 'paid', label: 'Paid', color: 'var(--accent-primary)' },
              { key: 'sick', label: 'Sick', color: 'var(--accent-warning)' },
              { key: 'unpaid', label: 'Unpaid', color: 'var(--accent-info)' },
            ].map(({ key, label, color }) => {
              const bal = leaveBalance[key as keyof typeof leaveBalance];
              const pct = bal.total > 0 ? ((bal.total - bal.remaining) / bal.total) * 100 : 0;
              return (
                <div key={key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">{label}</span>
                    <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{bal.remaining}/{bal.total}</span>
                  </div>
                  <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      </motion.div>

      {/* AI Nudge */}
      <NudgeCard />

      {/* Recent Activity */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Recent Activity</h3>
            <Clock className="w-4 h-4 text-[var(--text-muted)]" />
          </div>
          <div className="space-y-3">
            {data.recent_activity.slice(0, 4).map((act, i) => (
              <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-white/[0.02]">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-primary)] mt-1.5 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs text-[var(--text-primary)]">{act.description}</p>
                  <p className="text-[10px] text-[var(--text-muted)]">{new Date(act.timestamp).toLocaleString()}</p>
                </div>
              </div>
            ))}
            {data.recent_activity.length === 0 && (
              <p className="text-xs text-[var(--text-muted)] text-center py-4">No recent activity</p>
            )}
          </div>
        </GlassCard>
      </motion.div>

      {/* Pending Requests */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Pending Leaves</h3>
            <span className="text-xs bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] px-2 py-0.5 rounded-full">{data.pending_requests}</span>
          </div>
          <div className="text-center py-6">
            <p className="text-3xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{data.pending_requests}</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">requests pending approval</p>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}

function AdminDashboardView({ data }: { data: AdminDashboard }) {
  return (
    <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 [&>*]:break-inside-avoid [&>*]:mb-6">
      {/* Welcome Banner */}
      <motion.div variants={cardVariants} className="sm:col-span-2 lg:col-span-3">
        <GlassCard className="p-6 sm:p-8" glow="primary">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)]">Admin Dashboard</h2>
              <p className="text-[var(--text-secondary)] mt-1">{getCurrentDate()} · {getDayOfWeek()}</p>
            </div>
            <div className="flex gap-3">
              <a href="/admin/employees"><Button variant="secondary" size="sm"><Users className="w-4 h-4" /> Employees</Button></a>
              <a href="/admin/approvals"><Button variant="primary" size="sm"><CheckCircle className="w-4 h-4" /> Approvals</Button></a>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Quick Stats */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--accent-primary)]/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-[var(--accent-primary)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{data.total_employees}</p>
              <p className="text-xs text-[var(--text-muted)]">Total Employees</p>
            </div>
          </div>
          <div className="flex justify-between text-xs mt-3">
            <span className="text-[var(--text-muted)]">Active</span>
            <span className="text-[var(--accent-success)]">{data.active_employees}</span>
          </div>
        </GlassCard>
      </motion.div>

      {/* Pending Leaves */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Pending Approvals</h3>
            <a href="/admin/approvals" className="text-xs text-[var(--accent-primary)] hover:text-indigo-400">View All</a>
          </div>
          <div className="space-y-3">
            {data.pending_leaves.slice(0, 3).map((leave) => (
              <div key={leave.id} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02]">
                <div>
                  <p className="text-sm text-[var(--text-primary)]">{leave.employee_name}</p>
                  <p className="text-xs text-[var(--text-muted)]">{leave.leave_type} · {leave.days}d</p>
                </div>
                <StatusBadge variant="pending">pending</StatusBadge>
              </div>
            ))}
            {data.pending_leaves.length === 0 && (
              <p className="text-xs text-[var(--text-muted)] text-center py-4">All caught up!</p>
            )}
          </div>
        </GlassCard>
      </motion.div>

      {/* Burnout Alerts */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6 border-amber-500/20">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Burnout Alerts</h3>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="space-y-3">
            {data.burnout_alerts.slice(0, 3).map((alert, i) => (
              <div key={i} className="p-2 rounded-lg bg-white/[0.02]">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-[var(--text-primary)]">{alert.employee_name}</p>
                  <StatusBadge variant={alert.severity as 'high' | 'medium' | 'watch'}>{alert.severity}</StatusBadge>
                </div>
                <p className="text-[10px] text-[var(--text-muted)] mt-1">{alert.signal}</p>
              </div>
            ))}
            {data.burnout_alerts.length === 0 && (
              <p className="text-xs text-[var(--text-muted)] text-center py-4">No alerts</p>
            )}
          </div>
        </GlassCard>
      </motion.div>

      {/* Recent Activity */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Recent Activity</h3>
          </div>
          <div className="space-y-3">
            {data.recent_activity.slice(0, 4).map((act, i) => (
              <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-white/[0.02]">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-primary)] mt-1.5 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs text-[var(--text-primary)]">{act.description}</p>
                  <p className="text-[10px] text-[var(--text-muted)]">{new Date(act.timestamp).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </motion.div>

      {/* Department Health */}
      <motion.div variants={cardVariants}>
        <GlassCard hover className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Department Health</h3>
            <a href="/admin/analytics" className="text-xs text-[var(--accent-primary)] hover:text-indigo-400">Details</a>
          </div>
          <div className="space-y-3">
            {data.department_health.map((dept) => (
              <div key={dept.department}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[var(--text-secondary)]">{dept.department}</span>
                  <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{dept.score}%</span>
                </div>
                <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${dept.score}%`, backgroundColor: dept.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}

function CheckInButton() {
  const checkin = useCheckin();
  return (
    <Button size="lg" className="w-full sm:w-auto" onClick={() => checkin.mutate(undefined)} isLoading={checkin.isPending}>
      <LogIn className="w-5 h-5" /> Check In
    </Button>
  );
}

function CheckOutButton() {
  const checkout = useCheckout();
  return (
    <Button size="lg" variant="secondary" className="w-full sm:w-auto" onClick={() => checkout.mutate(undefined)} isLoading={checkout.isPending}>
      <LogOut className="w-5 h-5" /> Check Out
    </Button>
  );
}

function NudgeCard() {
  const { data: nudgeData } = useNudges(true);
  const nudge = nudgeData?.nudges?.[0];

  return (
    <motion.div variants={cardVariants}>
      <GlassCard hover className="p-6 border-cyan-500/20 relative overflow-hidden">
        <span className="absolute top-3 right-3 text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-2 py-0.5">AI</span>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-[var(--text-primary)]">AI Nudge</h3>
            <p className="text-xs text-[var(--text-muted)]">AI-powered insight</p>
          </div>
        </div>
        {nudge ? (
          <p className="text-sm text-[var(--text-secondary)]">{nudge.message}</p>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No nudges right now. You&apos;re doing great!</p>
        )}
        <div className="mt-4">
          <a href="/leave" className="text-xs text-[var(--accent-primary)] hover:text-indigo-400">View All Nudges</a>
        </div>
      </GlassCard>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) return <DashboardLoading />;

  if (error) {
    return (
      <ErrorBoundary>
        <GlassCard className="p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-[var(--text-primary)] mb-2">Unable to load dashboard</h2>
          <p className="text-sm text-[var(--text-secondary)]">Please check your connection and try again.</p>
        </GlassCard>
      </ErrorBoundary>
    );
  }

  if (!data?.data) return <DashboardLoading />;

  const dashboardData = data.data;

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show">
        {'pending_leaves' in dashboardData ? (
          <AdminDashboardView data={dashboardData as AdminDashboard} />
        ) : (
          <EmployeeDashboardView data={dashboardData as EmployeeDashboard} />
        )}
      </motion.div>
    </ErrorBoundary>
  );
}
