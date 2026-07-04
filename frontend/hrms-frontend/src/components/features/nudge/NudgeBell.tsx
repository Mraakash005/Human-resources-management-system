'use client';
import { useState } from 'react';
import { Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { formatTime } from '@/lib/utils';
import { useNudges, useMarkNudgeRead } from '@/hooks/useApi';

export function NudgeBell() {
  const [open, setOpen] = useState(false);
  const { data: nudgeData } = useNudges(false);
  const markRead = useMarkNudgeRead();
  const nudges = nudgeData?.nudges || [];
  const unreadCount = nudgeData?.unread_count || 0;

  const markAllRead = () => {
    nudges.filter(n => !n.read).forEach(n => markRead.mutate(n.id));
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--glass-bg-hover)] hover:text-[var(--text-primary)] transition-all"
      >
        <motion.div
          animate={unreadCount > 0 ? { rotate: [0, -10, 10, -10, 10, 0] } : {}}
          transition={{ duration: 0.5 }}
        >
          <Bell className="w-5 h-5" />
        </motion.div>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-bold">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="absolute right-0 top-12 w-80 rounded-2xl border border-white/[0.08] bg-[var(--bg-surface)] shadow-[0_8px_40px_rgba(0,0,0,0.5)] z-50 overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-white/[0.06]">
                <h3 className="font-semibold text-[var(--text-primary)]">Notifications</h3>
                {unreadCount > 0 && (
                  <button onClick={markAllRead} className="text-xs text-[var(--accent-primary)] hover:text-indigo-400">
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto">
                {nudges.length === 0 ? (
                  <div className="p-6 text-center text-sm text-[var(--text-muted)]">No notifications</div>
                ) : (
                  nudges.map(nudge => (
                    <div
                      key={nudge.id}
                      className={cn(
                        'p-4 border-b border-white/[0.06] hover:bg-white/[0.02] transition-colors',
                        !nudge.read && 'bg-white/[0.02]'
                      )}
                    >
                      <p className="text-sm text-[var(--text-primary)]">{nudge.message}</p>
                      <p className="text-xs text-[var(--text-muted)] mt-1">{formatTime(nudge.created_at)}</p>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
