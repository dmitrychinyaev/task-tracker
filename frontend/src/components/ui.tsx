import type { ReactNode } from 'react';
import { useI18n, statusLabel, priorityLabel } from '../i18n';
import type { Tag } from '../types';

export function Loading() {
  const { t } = useI18n();
  return <div className="muted">{t('common.loading')}</div>;
}

export function ErrorBanner({ message }: { message: string }) {
  if (!message) return null;
  return <div className="error-banner">{message}</div>;
}

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const { lang } = useI18n();
  const cls =
    status === 'blocked' ? 'badge blocked' : status === 'done' ? 'badge done' : 'badge';
  return <span className={cls}>{statusLabel(lang, status)}</span>;
}

export function PriorityBadge({ priority }: { priority?: string | null }) {
  const { lang } = useI18n();
  if (!priority) return null;
  return <span className={`badge p-${priority}`}>{priorityLabel(lang, priority)}</span>;
}

export function TagPills({ tags }: { tags: Tag[] }) {
  if (!tags.length) return null;
  return (
    <div className="tag-list">
      {tags.map((t) => (
        <span key={t.id} className="tag-pill">
          {t.name}
        </span>
      ))}
    </div>
  );
}

export function formatDateTime(s?: string | null): string {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString();
}

export function formatDate(s?: string | null): string {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleDateString();
}

export function formatDeadline(s?: string | null): string {
  if (!s) return '';
  const d = new Date(s + 'T00:00:00');
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
}
