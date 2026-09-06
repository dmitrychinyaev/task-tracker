import type {
  Assignee,
  Comment,
  GeneratePromptPayload,
  ImageMeta,
  PromptDraft,
  Sprint,
  Tag,
  TaskCreatePayload,
  TaskDetail,
  TaskSummary,
  TaskUpdatePayload,
} from './types';

const BASE = '';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isForm = options.body instanceof FormData;
  const res = await fetch(BASE + path, {
    ...options,
    headers: isForm
      ? options.headers
      : { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail.map((d: { msg?: string }) => d.msg).join('; ');
      }
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.blob()) as unknown as T;
}

function buildQuery(params?: Record<string, string | number | undefined | null>): string {
  if (!params) return '';
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v));
  });
  const qs = q.toString();
  return qs ? `?${qs}` : '';
}

export function imageUrl(id: number): string {
  return `${BASE}/api/images/${id}`;
}

export const api = {
  // ---- Assignees ----
  listAssignees: () => request<Assignee[]>('/api/assignees'),
  createAssignee: (d: { name: string; role?: string | null; note?: string | null }) =>
    request<Assignee>('/api/assignees', { method: 'POST', body: JSON.stringify(d) }),
  updateAssignee: (id: number, d: { name?: string; role?: string | null; note?: string | null }) =>
    request<Assignee>(`/api/assignees/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  deleteAssignee: (id: number) => request<void>(`/api/assignees/${id}`, { method: 'DELETE' }),

  // ---- Tags ----
  listTags: () => request<Tag[]>('/api/tags'),
  createTag: (d: { name: string }) =>
    request<Tag>('/api/tags', { method: 'POST', body: JSON.stringify(d) }),
  deleteTag: (id: number) => request<void>(`/api/tags/${id}`, { method: 'DELETE' }),

  // ---- Sprints ----
  listSprints: () => request<Sprint[]>('/api/sprints'),
  createSprint: (d: {
    name: string;
    start_date: string;
    end_date: string;
    status?: string;
    description?: string | null;
  }) => request<Sprint>('/api/sprints', { method: 'POST', body: JSON.stringify(d) }),
  updateSprint: (id: number, d: Partial<Sprint>) =>
    request<Sprint>(`/api/sprints/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  deleteSprint: (id: number) => request<void>(`/api/sprints/${id}`, { method: 'DELETE' }),

  // ---- Tasks ----
  listTasks: (params?: Record<string, string | number | undefined | null>) =>
    request<TaskSummary[]>(`/api/tasks${buildQuery(params)}`),
  getTask: (id: number) => request<TaskDetail>(`/api/tasks/${id}`),
  createTask: (d: TaskCreatePayload) =>
    request<TaskDetail>('/api/tasks', { method: 'POST', body: JSON.stringify(d) }),
  updateTask: (id: number, d: TaskUpdatePayload) =>
    request<TaskDetail>(`/api/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  moveTask: (id: number, status: string, blocking_reason?: string) =>
    request<TaskDetail>(`/api/tasks/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ status, blocking_reason }),
    }),
  addToBoard: (id: number, status: string) =>
    request<TaskDetail>(`/api/tasks/${id}/add-to-board`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),
  moveToBacklog: (id: number) =>
    request<TaskDetail>(`/api/tasks/${id}/move-to-backlog`, { method: 'POST' }),
  addComment: (id: number, text: string) =>
    request<Comment>(`/api/tasks/${id}/comments`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  deleteTask: (id: number) => request<void>(`/api/tasks/${id}`, { method: 'DELETE' }),

  // ---- Images ----
  uploadImage: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return request<ImageMeta>('/api/images', { method: 'POST', body: fd });
  },

  // ---- Reports ----
  taskReportUrl: (id: number) => `${BASE}/api/reports/task/${id}`,
  kanbanReportUrl: () => `${BASE}/api/reports/kanban`,
  sprintReportUrl: (id: number) => `${BASE}/api/reports/sprint/${id}`,
  activityReportUrl: (start?: string, end?: string) =>
    `${BASE}/api/reports/activity${buildQuery({ start, end })}`,

  // ---- Prompts ----
  generatePrompt: (d: GeneratePromptPayload) =>
    request<{ generated_prompt: string; role: string }>('/api/prompts/generate', {
      method: 'POST',
      body: JSON.stringify(d),
    }),
  listDrafts: () => request<PromptDraft[]>('/api/prompts/drafts'),
  createDraft: (d: Partial<PromptDraft>) =>
    request<PromptDraft>('/api/prompts/drafts', { method: 'POST', body: JSON.stringify(d) }),
  updateDraft: (id: number, d: Partial<PromptDraft>) =>
    request<PromptDraft>(`/api/prompts/drafts/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  deleteDraft: (id: number) => request<void>(`/api/prompts/drafts/${id}`, { method: 'DELETE' }),
};
