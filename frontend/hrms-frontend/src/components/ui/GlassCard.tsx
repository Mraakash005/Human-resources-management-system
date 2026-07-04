'use client';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  glow?: 'none' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
  hover?: boolean;
  onClick?: () => void;
}

const glowMap = {
  none: '',
  primary: 'shadow-[0_0_24px_rgba(99,102,241,0.25)]',
  success: 'shadow-[0_0_20px_rgba(16,185,129,0.2)]',
  warning: 'shadow-[0_0_20px_rgba(245,158,11,0.2)]',
  danger: 'shadow-[0_0_20px_rgba(239,68,68,0.2)]',
  info: 'shadow-[0_0_20px_rgba(6,182,212,0.2)]',
};

export function GlassCard({ children, className, glow = 'none', hover = false, onClick }: GlassCardProps) {
  return (
    <motion.div
      whileHover={hover ? { y: -2, scale: 1.005 } : undefined}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      className={cn(
        'relative rounded-2xl border border-white/[0.08] bg-white/[0.04]',
        'backdrop-blur-xl shadow-[0_4px_24px_rgba(0,0,0,0.4)]',
        hover && 'cursor-pointer hover:border-white/[0.14] hover:bg-white/[0.07] transition-all duration-200',
        glowMap[glow],
        className
      )}
    >
      <div className="absolute inset-x-0 top-0 h-px rounded-t-2xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      {children}
    </motion.div>
  );
}
