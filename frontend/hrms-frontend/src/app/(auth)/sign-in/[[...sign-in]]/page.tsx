'use client';

import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center p-4">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-200px] left-[-200px] w-[600px] h-[600px] rounded-full opacity-[0.08]"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,1) 0%, transparent 70%)' }} />
        <div className="absolute bottom-[-150px] right-[-150px] w-[500px] h-[500px] rounded-full opacity-[0.06]"
          style={{ background: 'radial-gradient(circle, rgba(6,182,212,1) 0%, transparent 70%)' }} />
      </div>
      
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-[var(--accent-primary)] flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">H</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Welcome back</h1>
          <p className="text-[var(--text-secondary)] mt-1">Sign in to your workspace</p>
        </div>
        
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] backdrop-blur-xl p-6 shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
          <SignIn
            appearance={{
              elements: {
                rootBox: 'w-full',
                card: 'bg-transparent shadow-none border-none',
                headerTitle: 'text-[var(--text-primary)]',
                headerSubtitle: 'text-[var(--text-secondary)]',
                socialButtonsBlockButton: 'bg-white/[0.05] border-white/[0.08] text-[var(--text-primary)] hover:bg-white/[0.08]',
                formFieldLabel: 'text-[var(--text-secondary)]',
                formFieldInput: 'bg-white/[0.05] border-white/[0.08] text-[var(--text-primary)]',
                footerActionLink: 'text-[var(--accent-primary)]',
                button: 'bg-[var(--accent-primary)] hover:bg-indigo-500',
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
