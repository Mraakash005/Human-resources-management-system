'use client';
import { usePathname } from 'next/navigation';
import { Search, Menu } from 'lucide-react';
import { NudgeBell } from '@/components/features/nudge/NudgeBell';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/attendance': 'My Attendance',
  '/leave': 'Leave & Time Off',
  '/payroll': 'Payroll',
  '/chat': 'Team Chat',
  '/admin/employees': 'Employee Management',
  '/admin/approvals': 'Leave Approvals',
  '/admin/analytics': 'Analytics',
  '/admin/audit': 'Audit Logs',
};

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const pathname = usePathname();
  const title = pageTitles[pathname] || 'HRMS';

  return (
    <header className="h-16 bg-[var(--bg-surface)]/80 backdrop-blur-sm border-b border-white/[0.06] flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="lg:hidden text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--glass-bg-hover)] hover:text-[var(--text-primary)] transition-all">
          <Search className="w-5 h-5" />
        </button>
        <NudgeBell />
      </div>
    </header>
  );
}
