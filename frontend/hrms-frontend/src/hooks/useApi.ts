'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { apiGet, apiPost, apiPatch } from '@/lib/api';
import type {
  ApiResponse,
  PaginatedResponse,
  EmployeeProfile,
  EmployeeDashboard,
  AdminDashboard,
  TodayAttendance,
  AttendanceCalendarMonth,
  HeatmapResponse,
  WeeklyViewResponse,
  LeaveResponse,
  LeaveBalanceSummary,
  LeaveApproval,
  LeaveCreate,
  ConversationalLeaveMessage,
  ConversationalLeaveResponse,
  PayrollRunResponse,
  SalaryStructureResponse,
  PayStubDownloadResponse,
  ChatChannelResponse,
  ChatMessageResponse,
  ChatMessageCreate,
  UnreadCountResponse,
  NudgeListResponse,
  BurnoutAlertEntry,
  TeamHealthScore,
} from '@/types';

const API = '/api/v1';

function useToken() {
  const { getToken } = useAuth();
  return async (): Promise<string> => {
    const token = await getToken();
    return token || '';
  };
}

export function useDashboard() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<{ role: string; data: EmployeeDashboard | AdminDashboard }>(`${API}/dashboard/dashboard`, token);
    },
    staleTime: 30000,
  });
}

export function useTodayAttendance() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['attendance', 'today'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<TodayAttendance>>(`${API}/attendance/today`, token);
    },
  });
}

export function useAttendanceCalendar(year?: number, month?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['attendance', 'calendar', year, month],
    queryFn: async () => {
      const token = await getToken();
      const params = new URLSearchParams();
      if (year) params.set('year', String(year));
      if (month) params.set('month', String(month));
      const qs = params.toString();
      return apiGet<ApiResponse<AttendanceCalendarMonth>>(`${API}/attendance/calendar${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useAttendanceHeatmap(year?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['attendance', 'heatmap', year],
    queryFn: async () => {
      const token = await getToken();
      const params = year ? `?year=${year}` : '';
      return apiGet<ApiResponse<HeatmapResponse>>(`${API}/attendance/heatmap${params}`, token);
    },
  });
}

export function useAttendanceWeekly() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['attendance', 'weekly'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<WeeklyViewResponse>>(`${API}/attendance/weekly`, token);
    },
  });
}

export function useCheckin() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data?: { lat?: number; lng?: number; method?: string }) => {
      const token = await getToken();
      return apiPost(`${API}/attendance/checkin`, data || {}, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['attendance'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useCheckout() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      return apiPost(`${API}/attendance/checkout`, {}, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['attendance'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useLeaveRequests(params?: { page?: number; limit?: number; status?: string }) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['leave', 'requests', params],
    queryFn: async () => {
      const token = await getToken();
      const sp = new URLSearchParams();
      if (params?.page) sp.set('page', String(params.page));
      if (params?.limit) sp.set('limit', String(params.limit));
      if (params?.status) sp.set('status', params.status);
      const qs = sp.toString();
      return apiGet<PaginatedResponse<LeaveResponse>>(`${API}/leave${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useLeaveBalance(year?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['leave', 'balance', year],
    queryFn: async () => {
      const token = await getToken();
      const params = year ? `?year=${year}` : '';
      return apiGet<ApiResponse<LeaveBalanceSummary>>(`${API}/leave/balance${params}`, token);
    },
  });
}

export function useCreateLeave() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: LeaveCreate) => {
      const token = await getToken();
      return apiPost<ApiResponse<LeaveResponse>>(`${API}/leave`, data, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leave'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useApproveLeave() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ leaveId, data }: { leaveId: string; data: LeaveApproval }) => {
      const token = await getToken();
      return apiPatch(`${API}/leave/${leaveId}/approve`, data, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leave'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useCancelLeave() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (leaveId: string) => {
      const token = await getToken();
      return apiPatch(`${API}/leave/${leaveId}/cancel`, {}, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leave'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useLeaveAdvisor() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['leave', 'advisor'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<Array<{ title: string; message: string; priority: string }>>>(`${API}/leave/advisor`, token);
    },
  });
}

export function useConversationalLeave() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async (data: ConversationalLeaveMessage) => {
      const token = await getToken();
      return apiPost<ConversationalLeaveResponse>(`${API}/leave/nlp/chat`, data, token);
    },
  });
}

export function useGenerateLeaveEmail() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async (data: { name: string; department?: string; leave_type: string; start_date: string; end_date: string; reason: string }) => {
      const token = await getToken();
      return apiPost<{ fallback: boolean; email: string }>(`${API}/leave/nlp/generate-leave-email`, data, token);
    },
  });
}

export function usePayroll(month?: number, year?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['payroll', month, year],
    queryFn: async () => {
      const token = await getToken();
      const params = new URLSearchParams();
      if (month) params.set('month', String(month));
      if (year) params.set('year', String(year));
      const qs = params.toString();
      return apiGet<ApiResponse<PayrollRunResponse>>(`${API}/payroll/me${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useSalaryStructure() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['payroll', 'salary'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<SalaryStructureResponse>>(`${API}/payroll/me/salary`, token);
    },
  });
}

export function usePayStubDownload(month?: number, year?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['payroll', 'stub', month, year],
    queryFn: async () => {
      const token = await getToken();
      const params = new URLSearchParams();
      if (month) params.set('month', String(month));
      if (year) params.set('year', String(year));
      const qs = params.toString();
      return apiGet<ApiResponse<PayStubDownloadResponse>>(`${API}/payroll/me/stub${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useChatChannels() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['chat', 'channels'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<ChatChannelResponse[]>>(`${API}/chat/channels`, token);
    },
  });
}

export function useChatMessages(channelId: string | null, limit = 50, offset = 0) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['chat', 'messages', channelId, limit, offset],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<ChatMessageResponse[]>>(`${API}/chat/messages?channel_id=${channelId}&limit=${limit}&offset=${offset}`, token);
    },
    enabled: !!channelId,
  });
}

export function useSendMessage() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: ChatMessageCreate) => {
      const token = await getToken();
      return apiPost<ApiResponse<ChatMessageResponse>>(`${API}/chat/messages`, data, token);
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ['chat', 'messages', variables.channel_id] });
    },
  });
}

export function useUnreadCounts() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['chat', 'unread'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<UnreadCountResponse[]>>(`${API}/chat/unread`, token);
    },
    refetchInterval: 10000,
  });
}

export function useNudges(unreadOnly = false) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['nudges', unreadOnly],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<NudgeListResponse>(`${API}/nudges?unread_only=${unreadOnly}`, token);
    },
  });
}

export function useMarkNudgeRead() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (nudgeId: string) => {
      const token = await getToken();
      return apiPatch(`${API}/nudges/${nudgeId}/read`, {}, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nudges'] });
    },
  });
}

export function useTeamHealth(department: string, month?: number, year?: number) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['analytics', 'team-health', department, month, year],
    queryFn: async () => {
      const token = await getToken();
      const params = new URLSearchParams({ department });
      if (month) params.set('month', String(month));
      if (year) params.set('year', String(year));
      return apiGet<TeamHealthScore>(`${API}/analytics/team-health?${params.toString()}`, token);
    },
    enabled: !!department,
  });
}

export function useBurnoutDashboard(department?: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['analytics', 'burnout', department],
    queryFn: async () => {
      const token = await getToken();
      const params = department ? `?department=${department}` : '';
      return apiGet<{ alerts: BurnoutAlertEntry[]; total: number }>(`${API}/analytics/burnout-dashboard${params}`, token);
    },
  });
}

export function useEmployees(params?: { page?: number; limit?: number; department?: string; search?: string }) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['employees', params],
    queryFn: async () => {
      const token = await getToken();
      const sp = new URLSearchParams();
      if (params?.page) sp.set('page', String(params.page));
      if (params?.limit) sp.set('limit', String(params.limit));
      if (params?.department) sp.set('department', params.department);
      if (params?.search) sp.set('search', params.search);
      const qs = sp.toString();
      return apiGet<PaginatedResponse<EmployeeProfile>>(`${API}/employees${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useAllPayroll(params?: { page?: number; limit?: number; month?: number; year?: number }) {
  const getToken = useToken();
  return useQuery({
    queryKey: ['payroll', 'all', params],
    queryFn: async () => {
      const token = await getToken();
      const sp = new URLSearchParams();
      if (params?.page) sp.set('page', String(params.page));
      if (params?.limit) sp.set('limit', String(params.limit));
      if (params?.month) sp.set('month', String(params.month));
      if (params?.year) sp.set('year', String(params.year));
      const qs = sp.toString();
      return apiGet<PaginatedResponse<PayrollRunResponse>>(`${API}/payroll/all${qs ? `?${qs}` : ''}`, token);
    },
  });
}

export function useMyProfile() {
  const getToken = useToken();
  return useQuery({
    queryKey: ['employees', 'me'],
    queryFn: async () => {
      const token = await getToken();
      return apiGet<ApiResponse<EmployeeProfile>>(`${API}/employees/me`, token);
    },
  });
}
