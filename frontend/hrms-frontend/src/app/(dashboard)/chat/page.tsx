'use client';
import { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Hash, Send, Users, Paperclip, Smile, Calendar, MapPin, Clock } from 'lucide-react';
import { formatTime } from '@/lib/utils';
import { containerVariants, cardVariants } from '@/lib/animations';
import {
  useChatChannels,
  useChatMessages,
  useSendMessage,
  useUnreadCounts,
} from '@/hooks/useApi';
import { useAuth } from '@clerk/nextjs';
import { apiPost } from '@/lib/api';

function MeetingInviteCard({
  meeting,
  messageId,
  onRsvp,
}: {
  meeting: {
    title: string;
    date: string;
    time: string;
    duration_minutes: number;
    location: string;
    agenda?: string;
  };
  messageId: string;
  onRsvp: (messageId: string, response: string) => void;
}) {
  return (
    <div className="border border-indigo-500/20 bg-indigo-500/5 rounded-2xl p-4 max-w-sm">
      <div className="flex items-center gap-2 text-indigo-400 text-sm font-semibold mb-2">
        <Calendar className="w-4 h-4" /> Meeting Invite
      </div>
      <p className="font-medium text-[var(--text-primary)]">{meeting.title}</p>
      <div className="mt-2 space-y-1 text-xs text-[var(--text-secondary)]">
        <p className="flex items-center gap-1">
          <Clock className="w-3 h-3" /> {meeting.date} · {meeting.time} ({meeting.duration_minutes} min)
        </p>
        <p className="flex items-center gap-1">
          <MapPin className="w-3 h-3" /> {meeting.location}
        </p>
        {meeting.agenda && <p className="italic text-[var(--text-muted)] mt-1">{meeting.agenda}</p>}
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => onRsvp(messageId, 'accepted')}
          className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs"
        >
          Accept
        </button>
        <button
          onClick={() => onRsvp(messageId, 'declined')}
          className="px-3 py-1.5 rounded-lg bg-red-500/15 text-red-400 border border-red-500/30 text-xs"
        >
          Decline
        </button>
        <button
          onClick={() => onRsvp(messageId, 'maybe')}
          className="px-3 py-1.5 rounded-lg bg-white/[0.05] text-[var(--text-secondary)] border border-white/[0.08] text-xs"
        >
          Maybe
        </button>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [activeChannel, setActiveChannel] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: channelsResponse, isLoading: channelsLoading } = useChatChannels();
  const channels = channelsResponse?.data ?? [];
  const resolvedChannel = activeChannel || channels[0]?.id || null;

  const { data: messagesResponse, isLoading: messagesLoading } = useChatMessages(resolvedChannel, limit, offset);
  const messages = messagesResponse?.data ?? [];

  const { data: unreadResponse } = useUnreadCounts();
  const unreadCounts = unreadResponse?.data ?? [];

  const sendMessage = useSendMessage();

  const markAsRead = useMutation({
    mutationFn: async (channelId: string) => {
      const token = await getToken();
      return apiPost(`/api/v1/chat/read/${channelId}`, {}, token ?? undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'unread'] });
    },
  });

  const rsvp = useMutation({
    mutationFn: async ({ messageId, response }: { messageId: string; response: string }) => {
      const token = await getToken();
      return apiPost(`/api/v1/chat/rsvp/${messageId}`, { response }, token ?? undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', resolvedChannel] });
    },
  });

  useEffect(() => {
    if (resolvedChannel) {
      markAsRead.mutate(resolvedChannel);
    }
  }, [resolvedChannel]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleChannelSelect = (channelId: string) => {
    setActiveChannel(channelId);
    setOffset(0);
  };

  const send = () => {
    if (!input.trim() || !resolvedChannel) return;
    sendMessage.mutate(
      { channel_id: resolvedChannel, body: input, message_type: 'text' },
      {
        onSuccess: () => {
          setInput('');
          queryClient.invalidateQueries({ queryKey: ['chat', 'messages', resolvedChannel] });
        },
      }
    );
  };

  const handleRsvp = (messageId: string, response: string) => {
    rsvp.mutate({ messageId, response });
  };

  const getUnreadCount = (channelId: string) => {
    const entry = unreadCounts.find((uc) => uc.channel_id === channelId);
    return entry?.unread_count ?? 0;
  };

  const activeChannelData = channels.find((ch) => ch.id === resolvedChannel);

  return (
    <ErrorBoundary>
      <motion.div variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={cardVariants}>
          <GlassCard className="p-0 overflow-hidden h-[calc(100vh-180px)]">
            <div className="flex h-full">
              {/* Channel List */}
              <div className="w-60 border-r border-white/[0.06] flex-shrink-0 hidden md:flex flex-col">
                <div className="p-4 border-b border-white/[0.06]">
                  <h3 className="font-semibold text-[var(--text-primary)] text-sm">Channels</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
                  {channelsLoading ? (
                    <div className="text-xs text-[var(--text-muted)] px-3 py-2">Loading channels...</div>
                  ) : (
                    channels.map((ch) => (
                      <button
                        key={ch.id}
                        onClick={() => handleChannelSelect(ch.id)}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all ${
                          resolvedChannel === ch.id
                            ? 'bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]'
                            : 'text-[var(--text-secondary)] hover:bg-white/[0.03]'
                        }`}
                      >
                        <Hash className="w-4 h-4 flex-shrink-0" />
                        <span className="flex-1 text-left truncate">{ch.name ?? ch.id}</span>
                        {getUnreadCount(ch.id) > 0 && (
                          <span className="w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                            {getUnreadCount(ch.id)}
                          </span>
                        )}
                      </button>
                    ))
                  )}
                  {/* HR Chatbot */}
                  <div className="mt-2 pt-2 border-t border-white/[0.06]">
                    <button className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-cyan-400 hover:bg-cyan-500/5">
                      <span className="text-cyan-400">✦</span>
                      <span className="flex-1 text-left">HR Chatbot</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Chat Area */}
              <div className="flex-1 flex flex-col min-w-0">
                <div className="h-14 border-b border-white/[0.06] flex items-center justify-between px-4">
                  <div className="flex items-center gap-2">
                    <Hash className="w-4 h-4 text-[var(--text-muted)]" />
                    <span className="font-medium text-[var(--text-primary)]">
                      {activeChannelData?.name ?? activeChannel ?? 'Select a channel'}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Users className="w-4 h-4" />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messagesLoading ? (
                    <div className="text-xs text-[var(--text-muted)] text-center py-8">Loading messages...</div>
                  ) : messages.length === 0 ? (
                    <div className="text-xs text-[var(--text-muted)] text-center py-8">No messages yet</div>
                  ) : (
                    messages.map((msg) =>
                      msg.message_type === 'meeting_invite' && msg.meeting_meta ? (
                        <div key={msg.id} className="flex items-start gap-3">
                          <Avatar name={msg.sender_name ?? 'Unknown'} size="sm" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-[var(--text-primary)]">
                                {msg.sender_name ?? 'Unknown'}
                              </span>
                              <span className="text-xs text-[var(--text-muted)]">
                                {formatTime(msg.created_at)}
                              </span>
                            </div>
                            <MeetingInviteCard
                              meeting={{
                                title: msg.meeting_meta.title,
                                date: msg.meeting_meta.date,
                                time: msg.meeting_meta.time,
                                duration_minutes: msg.meeting_meta.duration_minutes,
                                location: msg.meeting_meta.location,
                                agenda: msg.meeting_meta.agenda,
                              }}
                              messageId={msg.id}
                              onRsvp={handleRsvp}
                            />
                          </div>
                        </div>
                      ) : (
                        <div key={msg.id} className="flex items-start gap-3">
                          <Avatar name={msg.sender_name ?? 'Unknown'} size="sm" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-[var(--text-primary)]">
                                {msg.sender_name ?? 'Unknown'}
                              </span>
                              <span className="text-xs text-[var(--text-muted)]">
                                {formatTime(msg.created_at)}
                              </span>
                            </div>
                            <p className="text-sm text-[var(--text-secondary)] mt-0.5">{msg.body}</p>
                          </div>
                        </div>
                      )
                    )
                  )}
                  <div ref={bottomRef} />
                </div>

                <div className="border-t border-white/[0.06] p-3 flex items-center gap-2">
                  <button className="p-2 rounded-xl text-[var(--text-muted)] hover:bg-white/[0.05]">
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <button className="p-2 rounded-xl text-[var(--text-muted)] hover:bg-white/[0.05]">
                    <Smile className="w-5 h-5" />
                  </button>
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && send()}
                    className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                    placeholder={`Message #${activeChannelData?.name ?? activeChannel ?? ''}...`}
                  />
                  <Button onClick={send} disabled={!input.trim() || sendMessage.isPending} size="sm">
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Info Panel */}
              <div className="w-60 border-l border-white/[0.06] flex-shrink-0 hidden lg:flex flex-col">
                <div className="p-4 border-b border-white/[0.06]">
                  <h3 className="font-semibold text-[var(--text-primary)] text-sm">Members</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                  <div className="text-xs text-[var(--text-muted)] px-2 py-1.5">
                    Members list requires a separate API endpoint
                  </div>
                </div>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
