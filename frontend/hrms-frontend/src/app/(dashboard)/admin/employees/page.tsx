'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Avatar } from '@/components/ui/Avatar';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Search, Plus, Eye, Edit2, UserX, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { containerVariants, cardVariants } from '@/lib/animations';
import { useEmployees } from '@/hooks/useApi';

export default function EmployeesPage() {
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [debouncedSearch, setDebouncedSearch] = useState('');

  const deptParam = deptFilter === 'all' ? undefined : deptFilter;
  const { data, isLoading, isFetching } = useEmployees({
    page,
    limit: 10,
    department: deptParam,
    search: debouncedSearch || undefined,
  });

  const employees = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / 10));

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    const timeout = setTimeout(() => setDebouncedSearch(value), 400);
    return () => clearTimeout(timeout);
  };

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={cardVariants}>
          <GlassCard className="p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">Employee Management</h3>
                {isFetching && <Loader2 className="w-4 h-4 text-[var(--text-muted)] animate-spin" />}
              </div>
              <Button size="sm"><Plus className="w-4 h-4" /> Add Employee</Button>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                <input
                  value={search}
                  onChange={e => handleSearch(e.target.value)}
                  className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                  placeholder="Search by name or email..."
                />
              </div>
              <select
                value={deptFilter}
                onChange={e => { setDeptFilter(e.target.value); setPage(1); }}
                className="bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
              >
                <option value="all">All Departments</option>
                <option value="Engineering">Engineering</option>
                <option value="Design">Design</option>
                <option value="HR">HR</option>
                <option value="Marketing">Marketing</option>
              </select>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[var(--text-muted)] animate-spin" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      <th className="text-left py-3 text-xs text-[var(--text-muted)] font-medium">Employee</th>
                      <th className="text-left py-3 text-xs text-[var(--text-muted)] font-medium hidden sm:table-cell">Department</th>
                      <th className="text-left py-3 text-xs text-[var(--text-muted)] font-medium hidden md:table-cell">Role</th>
                      <th className="text-center py-3 text-xs text-[var(--text-muted)] font-medium">Status</th>
                      <th className="text-left py-3 text-xs text-[var(--text-muted)] font-medium hidden lg:table-cell">Joined</th>
                      <th className="text-right py-3 text-xs text-[var(--text-muted)] font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map(emp => (
                      <tr key={emp.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                        <td className="py-3">
                          <div className="flex items-center gap-3">
                            <Avatar name={emp.name} size="sm" />
                            <div>
                              <p className="font-medium text-[var(--text-primary)]">{emp.name}</p>
                              <p className="text-xs text-[var(--text-muted)]">{emp.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 text-[var(--text-secondary)] hidden sm:table-cell">{emp.department ?? '—'}</td>
                        <td className="py-3 text-[var(--text-secondary)] hidden md:table-cell">{emp.designation ?? '—'}</td>
                        <td className="py-3 text-center">
                          <StatusBadge variant={emp.is_active ? 'present' : 'pending'}>
                            {emp.is_active ? 'Active' : 'Inactive'}
                          </StatusBadge>
                        </td>
                        <td className="py-3 text-[var(--text-muted)] hidden lg:table-cell">
                          {emp.date_joined ? new Date(emp.date_joined).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '—'}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button className="p-1.5 rounded-lg hover:bg-white/[0.05] text-[var(--text-muted)] hover:text-[var(--text-primary)]"><Eye className="w-4 h-4" /></button>
                            <button className="p-1.5 rounded-lg hover:bg-white/[0.05] text-[var(--text-muted)] hover:text-[var(--text-primary)]"><Edit2 className="w-4 h-4" /></button>
                            <button className="p-1.5 rounded-lg hover:bg-white/[0.05] text-[var(--text-muted)] hover:text-red-400"><UserX className="w-4 h-4" /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {employees.length === 0 && (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-[var(--text-muted)]">
                          No employees found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
                <p className="text-xs text-[var(--text-muted)]">
                  Showing {((page - 1) * 10) + 1}–{Math.min(page * 10, total)} of {total}
                </p>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-[var(--text-secondary)] font-[family-name:var(--font-geist-mono)]">
                    {page} / {totalPages}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </GlassCard>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
