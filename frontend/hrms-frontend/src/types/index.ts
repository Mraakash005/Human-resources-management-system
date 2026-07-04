export type UserRole = 'admin' | 'employee';

export interface Employee {
  id: string;
  clerk_id: string;
  employee_id: string;
  name: string;
  email: string;
  department?: string;
  designation?: string;
  phone?: string;
  address?: string;
  profile_pic?: string;
  role: UserRole;
  date_joined: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type EmployeeProfile = Employee;

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  date: string;
  status: string;
  check_in?: string;
  check_out?: string;
  duration_hours?: number;
  check_in_method?: string;
}

export interface TodayAttendance {
  status: string;
  check_in?: string;
  check_out?: string;
  duration_hours?: number;
  can_check_in: boolean;
  can_check_out: boolean;
}

export interface AttendanceCalendarDay {
  date: string;
  status: string;
  check_in?: string;
  check_out?: string;
  duration_hours?: number;
}

export interface AttendanceCalendarMonth {
  year: number;
  month: number;
  days: AttendanceCalendarDay[];
  summary?: {
    total_working_days: number;
    present: number;
    absent: number;
    half_day: number;
    leave: number;
    weekend: number;
    holiday: number;
  };
}

export interface HeatmapResponse {
  year: number;
  data: Record<string, string>;
}

export interface WeeklyViewResponse {
  week_start: string;
  week_end: string;
  days: AttendanceCalendarDay[];
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name?: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  remarks?: string;
  admin_comment?: string;
  days?: number;
  email_sent?: boolean;
  reviewed_by?: string;
  reviewed_at?: string;
  created_at: string;
}

export type LeaveResponse = LeaveRequest;

export interface LeaveBalance {
  leave_type: string;
  total: number;
  used: number;
  remaining: number;
}

export interface LeaveBalanceSummary {
  year: number;
  balances: LeaveBalance[];
}

export interface LeaveApproval {
  status: 'approved' | 'rejected';
  comment?: string;
}

export interface LeaveCreate {
  leave_type: string;
  start_date: string;
  end_date: string;
  remarks?: string;
  formal_reason?: string;
  generated_email_body?: string;
  send_email?: boolean;
}

export interface ConversationalLeaveMessage {
  message: string;
  history?: Array<{ role: string; content: string }>;
}

export interface ConversationalLeaveResponse {
  reply: string;
  intent: string;
  extracted?: Record<string, unknown>;
  leave_id?: string;
}

export interface SalaryComponent {
  name: string;
  amount: number;
}

export interface PayrollRun {
  id: string;
  employee_id: string;
  month: number;
  year: number;
  gross_pay: number;
  deductions: number;
  net_pay: number;
  pay_stub_url?: string;
  components_snapshot: Record<string, unknown>;
  finalized_at: string;
}

export type PayrollRunResponse = PayrollRun;

export interface SalaryStructureResponse {
  employee_id: string;
  components: SalaryComponent[];
  effective_from?: string;
}

export interface PayStubDownloadResponse {
  download_url: string;
  month: number;
  year: number;
  filename: string;
}

export interface BurnoutAlertEntry {
  employee_id: string;
  employee_name?: string;
  signal: string;
  severity: 'high' | 'medium' | 'watch';
  value?: number;
  threshold?: number;
  created_at: string;
}

export interface TeamHealthScore {
  department: string;
  score: number;
  color: string;
  employee_count: number;
  risk_employees: number;
  month: number;
  year: number;
}

export interface Nudge {
  id: string;
  message: string;
  type: string;
  read: boolean;
  created_at: string;
}

export type NudgeResponse = Nudge;

export interface NudgeListResponse {
  nudges: NudgeResponse[];
  unread_count: number;
}

export interface AuditLogEntry {
  id: string;
  actor_id?: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  metadata?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export interface ChatChannelResponse {
  id: string;
  type: string;
  name?: string;
  department?: string;
  created_at: string;
}

export interface ChatMessageResponse {
  id: string;
  channel_id: string;
  sender_id: string;
  sender_name?: string;
  body: string;
  message_type: string;
  meeting_meta?: {
    title: string;
    date: string;
    time: string;
    duration_minutes: number;
    location: string;
    agenda?: string;
    rsvp_required?: boolean;
  };
  created_at: string;
}

export interface ChatMessageCreate {
  channel_id: string;
  body: string;
  message_type?: string;
  meeting_meta?: Record<string, unknown>;
}

export interface UnreadCountResponse {
  channel_id: string;
  unread_count: number;
}

export interface DashboardAttendance {
  status: string;
  check_in?: string;
  check_out?: string;
  duration_hours?: number;
  method?: string;
}

export interface DashboardLeaveBalance {
  paid: { total: number; used: number; remaining: number };
  sick: { total: number; used: number; remaining: number };
  unpaid: { total: number; used: number; remaining: number };
  bereavement: { total: number; used: number; remaining: number };
  medical: { total: number; used: number; remaining: number };
}

export interface DashboardRecentActivity {
  action: string;
  description: string;
  timestamp: string;
  icon?: string;
}

export interface DashboardPendingLeave {
  id: string;
  employee_name: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  days: number;
  remarks?: string;
  created_at: string;
}

export interface DashboardBurnoutAlert {
  employee_id: string;
  employee_name: string;
  signal: string;
  severity: string;
  value?: number;
  created_at: string;
}

export interface EmployeeDashboard {
  attendance: DashboardAttendance;
  leave_balance: DashboardLeaveBalance;
  recent_activity: DashboardRecentActivity[];
  pending_requests: number;
  total_employees: number;
}

export interface AdminDashboard {
  total_employees: number;
  active_employees: number;
  attendance_today: DashboardAttendance;
  pending_leaves: DashboardPendingLeave[];
  burnout_alerts: DashboardBurnoutAlert[];
  department_health: TeamHealthScore[];
  recent_activity: DashboardRecentActivity[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}
