import { cn } from '@/lib/utils';
import { getInitials } from '@/lib/utils';

interface AvatarProps {
  name: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeStyles = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-14 h-14 text-lg',
};

export function Avatar({ name, src, size = 'md', className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={cn('rounded-full object-cover', sizeStyles[size], className)}
      />
    );
  }

  return (
    <div className={cn(
      'rounded-full bg-[var(--accent-primary)]/20 border border-[var(--accent-primary)]/30',
      'flex items-center justify-center font-semibold text-[var(--accent-primary)]',
      sizeStyles[size],
      className
    )}>
      {getInitials(name)}
    </div>
  );
}
