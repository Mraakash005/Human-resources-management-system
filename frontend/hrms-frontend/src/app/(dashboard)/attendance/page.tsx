'use client';
import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { LogIn, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';
import { useTodayAttendance, useAttendanceCalendar, useAttendanceHeatmap, useCheckin, useCheckout } from '@/hooks/useApi';
import { containerVariants, cardVariants } from '@/lib/animations';

function LiveClock() {
  const [time, setTime] = useState('');
  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }));
    update();
    const i = setInterval(update, 1000);
    return () => clearInterval(i);
  }, []);
  return <span className="text-4xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-geist-mono)]">{time}</span>;
}

function MonthlyCalendar() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const { data, isLoading } = useAttendanceCalendar(year, month);

  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const statusMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (data?.data?.days) {
      data.data.days.forEach((d) => { map[d.date] = d.status; });
    }
    return map;
  }, [data]);

  const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' });

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'present': return 'bg-emerald-500/30';
      case 'absent': return 'bg-red-500/30';
      case 'leave': return 'bg-indigo-500/30';
      case 'half_day': return 'bg-amber-500/30';
      default: return '';
    }
  };

  return (
    <GlassCard className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[var(--text-primary)]">{monthName} {year}</h3>
        <div className="flex gap-2">
          <button onClick={prevMonth} className="p-1 rounded-lg hover:bg-white/[0.05]"><ChevronLeft className="w-4 h-4 text-[var(--text-secondary)]" /></button>
          <button onClick={nextMonth} className="p-1 rounded-lg hover:bg-white/[0.05]"><ChevronRight className="w-4 h-4 text-[var(--text-secondary)]" /></button>
        </div>
      </div>
      {isLoading ? (
        <Skeleton className="h-48 rounded-xl" />
      ) : (
        <>
          <div className="grid grid-cols-7 gap-1 text-center mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
              <div key={d} className="text-xs text-[var(--text-muted)] py-1">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: firstDay }).map((_, i) => <div key={`e-${i}`} />)}
            {days.map(day => {
              const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
              const status = statusMap[dateStr] || '';
              return (
                <div key={day} className={`aspect-square rounded-lg flex items-center justify-center text-xs text-[var(--text-primary)] cursor-pointer hover:bg-white/[0.05] ${getStatusBg(status)}`}>
                  {day}
                </div>
              );
            })}
          </div>
        </>
      )}
      <div className="flex items-center gap-4 mt-4 text-xs text-[var(--text-muted)]">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-500/30" /> Present</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500/30" /> Absent</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-indigo-500/30" /> Leave</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-500/30" /> Half-day</span>
      </div>
    </GlassCard>
  );
}

function AttendanceHeatmap() {
  const now = new Date();
  const { data, isLoading } = useAttendanceHeatmap(now.getFullYear());
  const heatmapData = data?.data?.data || {};

  const cells = useMemo(() => {
    const total = 371;
    return Array.from({ length: total }, (_, i) => {
      const date = new Date(now.getFullYear(), 0, 1 + i);
      const key = date.toISOString().split('T')[0];
      const status = heatmapData[key];
      let color = 'bg-white/[0.03]';
      if (status === 'present') color = 'bg-emerald-500/60';
      else if (status === 'half_day') color = 'bg-amber-500/40';
      else if (status === 'leave') color = 'bg-indigo-500/40';
      else if (status === 'absent') color = 'bg-red-500/40';
      return { key, color, date: key };
    });
  }, [heatmapData, now]);

  return (
    <GlassCard className="p-6">
      <h3 className="font-semibold text-[var(--text-primary)] mb-4">Attendance Heatmap</h3>
      {isLoading ? (
        <Skeleton className="h-32 rounded-xl" />
      ) : (
        <div className="overflow-x-auto">
          <div className="grid gap-0.5 min-w-[700px]" style={{ gridTemplateColumns: 'repeat(53, 1fr)' }}>
            {cells.map((cell) => (
              <div
                key={cell.key}
                className={`aspect-square rounded-sm cursor-pointer hover:ring-1 hover:ring-white/20 ${cell.color}`}
                title={cell.date}
              />
            ))}
          </div>
        </div>
      )}
      <div className="flex items-center gap-2 mt-3 text-xs text-[var(--text-muted)]">
        <span>Less</span>
        <span className="w-3 h-3 rounded-sm bg-white/[0.03]" />
        <span className="w-3 h-3 rounded-sm bg-emerald-500/20" />
        <span className="w-3 h-3 rounded-sm bg-emerald-500/40" />
        <span className="w-3 h-3 rounded-sm bg-emerald-500/60" />
        <span>More</span>
      </div>
    </GlassCard>
  );
}

export default function AttendancePage() {
  const { data: todayData, isLoading: todayLoading } = useTodayAttendance();
  const { data: weeklyData } = useAttendanceCalendar();
  const { data: heatmapData } = useAttendanceHeatmap(new Date().getFullYear());
  const checkin = useCheckin();
  const checkout = useCheckout();

  const today = todayData?.data;
  const isCheckedIn = today?.status !== 'not_checked_in';

  const weekly = weeklyData?.data?.days || [];
  const weekDays = ['M', 'T', 'W', 'T', 'F'];
  const todayDate = new Date();
  const mondayOffset = todayDate.getDay() === 0 ? -6 : 1 - todayDate.getDay();

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
        {/* Today's Status */}
        <motion.div variants={cardVariants}>
          {todayLoading ? (
            <Skeleton className="h-48 rounded-2xl" />
          ) : (
            <GlassCard className="p-6 sm:p-8" glow={isCheckedIn ? 'success' : 'primary'}>
              <div className="flex flex-col lg:flex-row gap-6">
                <div className="flex-1 text-center lg:text-left">
                  <LiveClock />
                  <div className="mt-4 flex flex-col sm:flex-row items-center gap-4">
                    <div className="flex-1">
                      {isCheckedIn ? (
                        <StatusBadge variant="present" pulse>
                          Checked In {today?.check_in ? `at ${new Date(today.check_in).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}` : ''}
                        </StatusBadge>
                      ) : (
                        <StatusBadge variant="absent">Not Checked In</StatusBadge>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {today?.can_check_in && (
                        <Button onClick={() => checkin.mutate(undefined)} size="lg" className="min-w-[180px]" isLoading={checkin.isPending}>
                          <LogIn className="w-5 h-5" /> Check In
                        </Button>
                      )}
                      {today?.can_check_out && (
                        <Button onClick={() => checkout.mutate(undefined)} variant="secondary" size="lg" className="min-w-[180px]" isLoading={checkout.isPending}>
                          <LogOut className="w-5 h-5" /> Check Out
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                <div className="lg:border-l lg:border-white/[0.06] lg:pl-6">
                  <p className="text-xs text-[var(--text-muted)] mb-3">This Week</p>
                  <div className="flex gap-2">
                    {weekDays.map((day, i) => {
                      const d = new Date(todayDate);
                      d.setDate(d.getDate() + mondayOffset + i);
                      const dateStr = d.toISOString().split('T')[0];
                      const dayData = weekly.find((w) => w.date === dateStr);
                      const isPresent = dayData?.status === 'present';
                      const isToday = d.toISOString().split('T')[0] === todayDate.toISOString().split('T')[0];
                      return (
                        <div key={i} className="flex flex-col items-center gap-1">
                          <span className="text-[10px] text-[var(--text-muted)]">{day}</span>
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs ${
                            isPresent ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : isToday ? 'bg-white/[0.06] text-[var(--text-primary)] border border-white/[0.1]' : 'bg-white/[0.03] text-[var(--text-muted)]'
                          }`}>
                            {isPresent ? '✓' : '—'}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </GlassCard>
          )}
        </motion.div>

        {/* Calendar & Heatmap */}
        <motion.div variants={cardVariants}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MonthlyCalendar />
            <AttendanceHeatmap />
          </div>
        </motion.div>

        {/* Stats */}
        {heatmapData?.data && (
          <motion.div variants={cardVariants}>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Present Days', value: Object.values(heatmapData.data.data).filter(s => s === 'present').length, color: 'text-emerald-400' },
                { label: 'Absent Days', value: Object.values(heatmapData.data.data).filter(s => s === 'absent').length, color: 'text-red-400' },
                { label: 'Half Days', value: Object.values(heatmapData.data.data).filter(s => s === 'half_day').length, color: 'text-amber-400' },
                { label: 'Leave Days', value: Object.values(heatmapData.data.data).filter(s => s === 'leave').length, color: 'text-cyan-400' },
              ].map((stat) => (
                <GlassCard key={stat.label} className="p-5">
                  <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
                  <p className={`text-3xl font-bold ${stat.color} font-[family-name:var(--font-geist-mono)] mt-1`}>{stat.value}</p>
                </GlassCard>
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>
    </ErrorBoundary>
  );
}
