'use client';

export function BgOrbs() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      <div
        className="absolute -top-[200px] -left-[200px] w-[600px] h-[600px] rounded-full opacity-[0.08]"
        style={{
          background: 'radial-gradient(circle, rgba(99,102,241,1) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute -bottom-[150px] -right-[150px] w-[500px] h-[500px] rounded-full opacity-[0.06]"
        style={{
          background: 'radial-gradient(circle, rgba(6,182,212,1) 0%, transparent 70%)',
        }}
      />
    </div>
  );
}
