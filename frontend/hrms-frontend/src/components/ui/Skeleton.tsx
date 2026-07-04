import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn(
      'animate-pulse rounded-xl bg-white/[0.05]',
      'relative overflow-hidden',
      'before:absolute before:inset-0 before:-translate-x-full',
      'before:animate-[shimmer_2s_infinite]',
      'before:bg-gradient-to-r before:from-transparent before:via-white/[0.08] before:to-transparent',
      className
    )} />
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 space-y-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

export function StatSkeleton() {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-5 space-y-3">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-10 w-16" />
      <Skeleton className="h-3 w-24" />
    </div>
  );
}
