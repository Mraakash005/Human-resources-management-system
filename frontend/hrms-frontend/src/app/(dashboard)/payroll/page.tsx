'use client';
import { useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Skeleton } from '@/components/ui/Skeleton';
import { Download, DollarSign } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import { containerVariants, cardVariants } from '@/lib/animations';
import { usePayroll, useSalaryStructure, usePayStubDownload } from '@/hooks/useApi';
import { apiGet } from '@/lib/api';
import type { PayrollRunResponse, SalaryComponent, ApiResponse } from '@/types';

const NOW = new Date();
const CURRENT_MONTH = NOW.getMonth() + 1;
const CURRENT_YEAR = NOW.getFullYear();

const MONTH_LABELS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function buildHistoryParams(): { month: number; year: number }[] {
  const params: { month: number; year: number }[] = [];
  let m = CURRENT_MONTH;
  let y = CURRENT_YEAR;
  for (let i = 0; i < 12; i++) {
    params.push({ month: m, year: y });
    m--;
    if (m < 1) { m = 12; y--; }
  }
  return params;
}

function usePayHistory() {
  const { getToken } = useAuth();
  const months = buildHistoryParams();
  return useQueries({
    queries: months.map(({ month, year }) => ({
      queryKey: ['payroll', month, year],
      queryFn: async () => {
        const token = await getToken();
        const params = new URLSearchParams({ month: String(month), year: String(year) });
        const res = await apiGet<ApiResponse<PayrollRunResponse>>(
          `/api/v1/payroll/me?${params.toString()}`,
          token ?? undefined
        );
        return res?.data ?? null;
      },
      staleTime: 60_000,
    })),
  });
}

function PayHistoryTable() {
  const history = usePayHistory();
  const isLoading = history.some(q => q.isLoading);
  const entries = history
    .map(q => q.data)
    .filter((e): e is PayrollRunResponse => e != null);

  if (isLoading) {
    return (
      <GlassCard className="p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 rounded-xl" />)}
        </div>
      </GlassCard>
    );
  }

  if (entries.length === 0) {
    return (
      <GlassCard className="p-6 text-center">
        <p className="text-sm text-[var(--text-muted)]">No payroll history found.</p>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="p-6 overflow-x-auto">
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Pay History</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/[0.06]">
            <th className="text-left py-2 text-xs text-[var(--text-muted)] font-medium">Period</th>
            <th className="text-right py-2 text-xs text-[var(--text-muted)] font-medium">Gross</th>
            <th className="text-right py-2 text-xs text-[var(--text-muted)] font-medium">Deductions</th>
            <th className="text-right py-2 text-xs text-[var(--text-muted)] font-medium">Net</th>
            <th className="text-right py-2 text-xs text-[var(--text-muted)] font-medium">PDF</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <HistoryRow key={`${entry.month}-${entry.year}`} entry={entry} />
          ))}
        </tbody>
      </table>
    </GlassCard>
  );
}

function HistoryRow({ entry }: { entry: PayrollRunResponse }) {
  const { data: stubData } = usePayStubDownload(entry.month, entry.year);

  const handleDownload = () => {
    const url = stubData?.data?.download_url;
    if (url) {
      window.open(url, '_blank');
    }
  };

  return (
    <tr className="border-b border-white/[0.03] hover:bg-white/[0.02]">
      <td className="py-3 text-[var(--text-primary)]">
        {MONTH_LABELS[entry.month - 1]} {entry.year}
      </td>
      <td className="py-3 text-right font-[family-name:var(--font-geist-mono)] text-[var(--text-primary)]">
        {formatCurrency(entry.gross_pay)}
      </td>
      <td className="py-3 text-right font-[family-name:var(--font-geist-mono)] text-[var(--accent-danger)]">
        -{formatCurrency(entry.deductions)}
      </td>
      <td className="py-3 text-right font-[family-name:var(--font-geist-mono)] text-[var(--accent-success)] font-semibold">
        {formatCurrency(entry.net_pay)}
      </td>
      <td className="py-3 text-right">
        {stubData?.data?.download_url && (
          <Button variant="ghost" size="sm" onClick={handleDownload}>
            <Download className="w-4 h-4" />
          </Button>
        )}
      </td>
    </tr>
  );
}

function SalarySimulator() {
  const [basic, setBasic] = useState(50000);
  const [hra, setHra] = useState(20000);
  const [bonus, setBonus] = useState(0);
  const [pfEnabled, setPfEnabled] = useState(true);

  const pf = pfEnabled ? Math.round(basic * 0.12) : 0;
  const gross = basic + hra + bonus;
  const tax = Math.max(0, (gross - 50000) * 0.1);
  const net = gross - pf - tax;

  return (
    <GlassCard className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="w-5 h-5 text-[var(--accent-primary)]" />
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Salary Simulator</h3>
      </div>
      <p className="text-xs text-[var(--accent-warning)] mb-4">Local simulation only — actual payroll is computed by HR.</p>

      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--text-secondary)]">Basic Salary</span>
            <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{formatCurrency(basic)}</span>
          </div>
          <input type="range" min={10000} max={200000} step={1000} value={basic} onChange={e => setBasic(+e.target.value)} className="w-full accent-[var(--accent-primary)]" />
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--text-secondary)]">HRA</span>
            <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{formatCurrency(hra)}</span>
          </div>
          <input type="range" min={0} max={100000} step={1000} value={hra} onChange={e => setHra(+e.target.value)} className="w-full accent-[var(--accent-primary)]" />
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--text-secondary)]">Performance Bonus</span>
            <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{formatCurrency(bonus)}</span>
          </div>
          <input type="range" min={0} max={50000} step={1000} value={bonus} onChange={e => setBonus(+e.target.value)} className="w-full accent-[var(--accent-primary)]" />
        </div>
        <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <input type="checkbox" checked={pfEnabled} onChange={e => setPfEnabled(e.target.checked)} className="accent-[var(--accent-primary)]" />
          Enable PF Deduction (12%)
        </label>
      </div>

      <div className="border-t border-white/[0.06] mt-4 pt-4 space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Gross Pay</span>
          <span className="text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{formatCurrency(gross)}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">PF Deduction</span>
          <span className="text-[var(--accent-danger)] font-[family-name:var(--font-geist-mono)]">-{formatCurrency(pf)}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Est. Tax</span>
          <span className="text-[var(--accent-danger)] font-[family-name:var(--font-geist-mono)]">-{formatCurrency(tax)}</span>
        </div>
        <div className="flex justify-between text-sm font-bold pt-2 border-t border-white/[0.06]">
          <span className="text-[var(--text-primary)]">Net Take-Home</span>
          <span className="text-[var(--accent-success)] font-[family-name:var(--font-geist-mono)]">{formatCurrency(net)}</span>
        </div>
      </div>
    </GlassCard>
  );
}

function CurrentMonthSalary() {
  const { data: payrollData, isLoading: payrollLoading } = usePayroll(CURRENT_MONTH, CURRENT_YEAR);
  const { data: salaryData, isLoading: salaryLoading } = useSalaryStructure();

  const payroll = payrollData?.data;
  const salary = salaryData?.data;

  if (payrollLoading || salaryLoading) {
    return (
      <GlassCard className="p-6">
        <Skeleton className="h-6 w-48 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-8 rounded-xl" />)}
        </div>
      </GlassCard>
    );
  }

  if (!payroll) {
    return (
      <GlassCard className="p-6 text-center">
        <DollarSign className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3" />
        <p className="text-sm text-[var(--text-secondary)]">No salary data for this month.</p>
      </GlassCard>
    );
  }

  const earnings = salary?.components || [];
  const deductions = Object.entries(payroll.components_snapshot || {})
    .filter(([k]) => k.toLowerCase().includes('pf') || k.toLowerCase().includes('tax') || k.toLowerCase().includes('deduction'))
    .map(([name, amount]) => ({ name, amount: Number(amount) }));

  return (
    <GlassCard className="p-6" glow="success">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            {MONTH_LABELS[payroll.month - 1]} {payroll.year}
          </h3>
          <p className="text-xs text-[var(--text-muted)]">Salary Breakdown</p>
        </div>
        <StatusBadge variant={payroll.finalized_at ? 'approved' : 'pending'}>
          {payroll.finalized_at ? 'Paid' : 'Pending'}
        </StatusBadge>
      </div>

      <div className="space-y-3">
        <p className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">Earnings</p>
        {earnings.map((comp: SalaryComponent) => (
          <div key={comp.name} className="flex justify-between">
            <span className="text-xs text-[var(--text-secondary)]">{comp.name}</span>
            <span className="text-sm font-[family-name:var(--font-geist-mono)] text-[var(--text-primary)]">{formatCurrency(comp.amount)}</span>
          </div>
        ))}
        <div className="flex justify-between border-t border-white/[0.06] pt-2">
          <span className="text-xs text-[var(--text-muted)]">Gross Pay</span>
          <span className="text-sm font-bold font-[family-name:var(--font-geist-mono)] text-[var(--text-primary)]">{formatCurrency(payroll.gross_pay)}</span>
        </div>

        {deductions.length > 0 && (
          <>
            <p className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider mt-3">Deductions</p>
            {deductions.map((d) => (
              <div key={d.name} className="flex justify-between">
                <span className="text-xs text-[var(--text-secondary)]">{d.name}</span>
                <span className="text-sm font-[family-name:var(--font-geist-mono)] text-[var(--accent-danger)]">-{formatCurrency(d.amount)}</span>
              </div>
            ))}
          </>
        )}

        <div className="flex justify-between border-t border-white/[0.06] pt-3">
          <span className="text-xs text-[var(--text-muted)]">Net Pay</span>
          <span className="text-lg font-bold font-[family-name:var(--font-geist-mono)] text-[var(--accent-success)]">{formatCurrency(payroll.net_pay)}</span>
        </div>
      </div>
    </GlassCard>
  );
}

export default function PayrollPage() {
  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={cardVariants}>
          <CurrentMonthSalary />
        </motion.div>

        <motion.div variants={cardVariants}>
          <PayHistoryTable />
        </motion.div>

        <motion.div variants={cardVariants}>
          <SalarySimulator />
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
