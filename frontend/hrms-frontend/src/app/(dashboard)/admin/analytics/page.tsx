'use client';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Avatar } from '@/components/ui/Avatar';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Loader2 } from 'lucide-react';
import { containerVariants, cardVariants } from '@/lib/animations';
import { useBurnoutDashboard, useTeamHealth } from '@/hooks/useApi';

const DEPARTMENTS = ['Engineering', 'Design', 'Marketing', 'HR'];

function TeamHealthGauge({ score, dept, employeeCount, riskEmployees }: { score: number; dept: string; employeeCount: number; riskEmployees: number }) {
  const color = score >= 75 ? 'var(--accent-success)' : score >= 50 ? 'var(--accent-warning)' : 'var(--accent-danger)';
  const pct = score;
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <GlassCard className="p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-[var(--text-muted)]">{dept}</p>
          <p className="text-3xl font-bold font-[family-name:var(--font-geist-mono)]" style={{ color }}>{score}</p>
          <p className="text-xs text-[var(--text-muted)]">Health Score</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-[var(--text-muted)]">{employeeCount} employees</span>
            {riskEmployees > 0 && (
              <span className="text-[10px] text-red-400">{riskEmployees} at risk</span>
            )}
          </div>
        </div>
        <div className="relative w-20 h-20">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            <circle cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={offset}
              className="transition-all duration-1000" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center text-lg font-bold" style={{ color }}>{score}</div>
        </div>
      </div>
    </GlassCard>
  );
}

function DepartmentHealthRow({ dept }: { dept: string }) {
  const { data, isLoading } = useTeamHealth(dept);
  if (isLoading || !data) return null;
  return (
    <TeamHealthGauge
      score={data.score}
      dept={data.department}
      employeeCount={data.employee_count}
      riskEmployees={data.risk_employees}
    />
  );
}

export default function AnalyticsPage() {
  const { data: burnoutData, isLoading: burnoutLoading } = useBurnoutDashboard();
  const alerts = burnoutData?.alerts ?? [];
  const totalAlerts = burnoutData?.total ?? alerts.length;

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        {/* Burnout Dashboard */}
        <motion.div variants={cardVariants}>
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Burnout Early Warning</h3>
              {burnoutLoading ? (
                <Loader2 className="w-4 h-4 text-[var(--text-muted)] animate-spin" />
              ) : (
                <StatusBadge variant="high" pulse>{totalAlerts} Alert{totalAlerts !== 1 ? 's' : ''}</StatusBadge>
              )}
            </div>

            {burnoutLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-[var(--text-muted)] animate-spin" />
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-[var(--text-muted)]">No burnout alerts at this time.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, i) => (
                  <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                    <div className="flex items-center gap-4">
                      <Avatar name={alert.employee_name ?? 'Employee'} />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-[var(--text-primary)]">{alert.employee_name ?? alert.employee_id}</p>
                          <StatusBadge variant={alert.severity}>{alert.severity}</StatusBadge>
                        </div>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5">{alert.signal}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="px-3 py-1.5 rounded-lg bg-white/[0.05] text-xs text-[var(--text-secondary)] hover:bg-white/[0.08]">Nudge</button>
                      <button className="px-3 py-1.5 rounded-lg bg-white/[0.05] text-xs text-[var(--text-secondary)] hover:bg-white/[0.08]">1:1</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </motion.div>

        {/* Team Health Scores */}
        <motion.div variants={cardVariants}>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Team Health Scores</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEPARTMENTS.map(dept => (
              <DepartmentHealthRow key={dept} dept={dept} />
            ))}
          </div>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
