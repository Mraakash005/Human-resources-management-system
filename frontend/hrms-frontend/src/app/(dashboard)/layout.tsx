'use client';
import { useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { BgOrbs } from '@/components/layout/BgOrbs';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthSync } from '@/hooks/useAuthSync';

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: true,
        retry: 1,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    return makeQueryClient();
  }
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const queryClient = getQueryClient();
  const { user, isLoaded, role, isAdmin } = useAuthSync();

  const userName = user?.firstName
    ? `${user.firstName} ${user.lastName || ''}`.trim()
    : isLoaded
      ? 'User'
      : '';
  const userRole = isAdmin ? 'Administrator' : 'Employee';

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-[var(--bg-base)]">
        <BgOrbs />

        {/* Desktop Sidebar */}
        <div className="hidden lg:block">
          <Sidebar role={role as 'admin' | 'employee'} userName={userName} userRole={userRole} />
        </div>

        {/* Mobile Sidebar Overlay */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 z-50 lg:hidden"
                onClick={() => setMobileMenuOpen(false)}
              />
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="fixed left-0 top-0 h-full z-50 lg:hidden"
              >
                <Sidebar role={role as 'admin' | 'employee'} userName={userName} userRole={userRole} />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Main content */}
        <div className="lg:ml-60 min-h-screen flex flex-col">
          <Navbar onMenuClick={() => setMobileMenuOpen(true)} />
          <main className="flex-1 relative z-10 p-4 sm:p-6">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </main>
          <footer className="h-10 bg-[var(--bg-surface)]/80 border-t border-white/[0.06] flex items-center justify-between px-6 text-xs text-[var(--text-muted)]">
            <span>v3.0.0</span>
            <span>© 2026 HRMS</span>
          </footer>
        </div>

        <Toaster
          position="top-right"
          theme="dark"
          toastOptions={{
            style: {
              background: 'var(--bg-surface)',
              border: '1px solid var(--glass-border)',
              color: 'var(--text-primary)',
            },
          }}
        />
      </div>
    </QueryClientProvider>
  );
}
