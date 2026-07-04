import { cn } from '@/lib/utils';

type BadgeVariant = 'approved' | 'pending' | 'rejected' | 'present' | 'absent' | 'half-day' | 'high' | 'medium' | 'watch' | 'info';

const variantStyles: Record<BadgeVariant, string> = {
  approved: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  present: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  pending: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  rejected: 'bg-red-500/15 text-red-400 border-red-500/30',
  absent: 'bg-red-500/15 text-red-400 border-red-500/30',
  high: 'bg-red-500/15 text-red-400 border-red-500/30',
  'half-day': 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
  watch: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  info: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
};

interface StatusBadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  pulse?: boolean;
}

export function StatusBadge({ variant, children, className, pulse }: StatusBadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border font-medium',
      variantStyles[variant],
      className
    )}>
      {pulse && (
        <span className={cn('w-1.5 h-1.5 rounded-full animate-pulse', {
          'bg-emerald-400': variant === 'approved' || variant === 'present',
          'bg-amber-400': variant === 'pending' || variant === 'medium',
          'bg-red-400': variant === 'rejected' || variant === 'absent' || variant === 'high',
          'bg-cyan-400': variant === 'watch' || variant === 'info',
          'bg-indigo-400': variant === 'half-day',
        })} />
      )}
      {children}
    </span>
  );
}
