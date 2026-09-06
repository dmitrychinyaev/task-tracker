export type TaskStatus =
  | 'backlog'
  | 'todo'
  | 'in_progress'
  | 'review'
  | 'qa'
  | 'blocked'
  | 'done';

export type Priority = 'low' | 'medium' | 'high' | 'critical';

export type SprintStatus = 'planned' | 'active' | 'completed' | 'cancelled';

export interface Assignee {
  id: number;
  name: string;
  role?: string | null;
  note?: string | null;
  created_at: string;
}

export interface Tag {
  id: number;
  name: string;
  created_at: string;
}

export interface Sprint {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  description?: string | null;
  created_at: string;
}

export type DescriptionBlock =
  | { type: 'text'; content: string }
  | { type: 'image'; image_id: number };

export interface TaskLink {
  id: number;
  task_id: number;
  label?: string | null;
  url: string;
}

export interface Comment {
  id: number;
  task_id: number;
  text: string;
  created_at: string;
}

export interface HistoryEvent {
  id: number;
  task_id: number;
  event_type: string;
  field_name?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  created_at: string;
}

export interface TaskSummary {
  id: number;
  title: string;
  assignee_id: number | null;
  assignee?: Assignee | null;
  status: string;
  priority?: string | null;
  sprint_id?: number | null;
  sprint?: Sprint | null;
  deadline?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  blocked_reason?: string | null;
  blocked_at?: string | null;
  previous_status?: string | null;
  is_on_board: boolean;
  is_archived: boolean;
  source?: string;
  is_inbox?: boolean;
  telegram_metadata?: Record<string, unknown> | null;
  tags: Tag[];
}

export interface TaskDetail extends TaskSummary {
  description: DescriptionBlock[];
  links: TaskLink[];
  comments: Comment[];
  history: HistoryEvent[];
}

export interface ImageMeta {
  id: number;
  original_name?: string | null;
  content_type: string;
  size: number;
  created_at: string;
}

export interface PromptDraft {
  id: number;
  source_text: string;
  role: string;
  title?: string | null;
  links?: string | null;
  context?: string | null;
  generated_prompt: string;
  ru_text?: string | null;
  en_text?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskLinkIn {
  label?: string | null;
  url: string;
}

export interface TaskCreatePayload {
  title: string;
  assignee_id: number;
  description?: DescriptionBlock[];
  priority?: Priority | null;
  sprint_id?: number | null;
  deadline?: string | null;
  tag_ids?: number[];
  links?: TaskLinkIn[];
}

export interface TaskUpdatePayload {
  title?: string;
  assignee_id?: number | null;
  description?: DescriptionBlock[];
  priority?: Priority | null;
  sprint_id?: number | null;
  deadline?: string | null;
  tag_ids?: number[];
  links?: TaskLinkIn[];
}

export interface GeneratePromptPayload {
  source_text?: string;
  role?: string;
  title?: string | null;
  links?: string | null;
  context?: string | null;
}
