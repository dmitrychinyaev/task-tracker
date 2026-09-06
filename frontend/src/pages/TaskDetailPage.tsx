import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, imageUrl } from '../api';
import { useI18n, statusLabel } from '../i18n';
import type { TaskDetail } from '../types';
import {
  ErrorBanner,
  Loading,
  StatusBadge,
  PriorityBadge,
  TagPills,
  formatDateTime,
  formatDeadline,
} from '../components/ui';

const STATUSES = ['backlog', 'todo', 'in_progress', 'review', 'qa', 'blocked', 'done'];

export default function TaskDetailPage() {
  const { id } = useParams();
  const taskId = Number(id);
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [comment, setComment] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getTask(taskId);
      setTask(data);
      setNewStatus(data.status);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    load();
  }, [load]);

  const applyStatus = async () => {
    if (!task || !newStatus || newStatus === task.status) return;
    setError('');
    try {
      if (newStatus === 'blocked') {
        const reason = window.prompt(t('board.blockReasonPrompt'));
        if (reason === null) return;
        await api.moveTask(task.id, newStatus, reason);
      } else {
        await api.moveTask(task.id, newStatus);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const addComment = async () => {
    if (!task || !comment.trim()) return;
    setError('');
    try {
      await api.addComment(task.id, comment.trim());
      setComment('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const removeTask = async () => {
    if (!task) return;
    if (!window.confirm(t('common.confirmDelete'))) return;
    setError('');
    try {
      await api.deleteTask(task.id);
      navigate('/board');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const moveToBacklog = async () => {
    if (!task) return;
    setError('');
    try {
      await api.moveToBacklog(task.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;
  if (!task) return <ErrorBanner message={error || t('common.error')} />;

  return (
    <div>
      <div className="toolbar">
        <Link className="btn secondary" to="/board">
          {t('common.back')}
        </Link>
        <Link className="btn secondary" to={`/tasks/${task.id}/edit`}>
          {t('common.edit')}
        </Link>
        <a className="btn secondary" href={api.taskReportUrl(task.id)}>
          {t('task.report')}
        </a>
        {task.is_inbox && (
          <button className="btn" onClick={moveToBacklog}>
            {t('inbox.moveToBacklog')}
          </button>
        )}
        <button className="btn danger" onClick={removeTask}>
          {t('task.delete')}
        </button>
      </div>

      <ErrorBanner message={error} />

      <div className="card">
        <h1 className="page-title" style={{ marginBottom: 8 }}>
          {task.title}
        </h1>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <StatusBadge status={task.status} />
          <PriorityBadge priority={task.priority} />
        </div>

        <div className="grid cols-2" style={{ marginTop: 16 }}>
          <div>
            <div className="muted">{t('task.assignee')}</div>
            <div>{task.assignee?.name ?? t('task.noAssignee')}</div>
          </div>
          <div>
            <div className="muted">{t('task.sprint')}</div>
            <div>{task.sprint?.name ?? '—'}</div>
          </div>
          <div>
            <div className="muted">{t('task.deadline')}</div>
            <div>{formatDeadline(task.deadline)}</div>
          </div>
          <div>
            <div className="muted">{t('task.updatedAt')}</div>
            <div>{formatDateTime(task.updated_at)}</div>
          </div>
        </div>

        {task.tags.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="muted" style={{ marginBottom: 6 }}>
              {t('task.tags')}
            </div>
            <TagPills tags={task.tags} />
          </div>
        )}

        {task.blocked_reason && (
          <div style={{ marginTop: 12 }}>
            <div className="muted">{t('task.blockedReason')}</div>
            <div>{task.blocked_reason}</div>
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.description')}</h3>
        {task.description.length === 0 ? (
          <div className="muted">{t('task.emptyDescription')}</div>
        ) : (
          task.description.map((block, i) =>
            block.type === 'text' ? (
              <p key={i} style={{ whiteSpace: 'pre-wrap' }}>
                {block.content}
              </p>
            ) : (
              <img
                key={i}
                src={imageUrl(block.image_id)}
                alt=""
                style={{ maxWidth: '100%', borderRadius: 8, marginBottom: 8 }}
              />
            ),
          )
        )}
      </div>
      {task.links.length > 0 && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>{t('task.links')}</h3>
          <ul>
            {task.links.map((link) => (
              <li key={link.id}>
                <a href={link.url} target="_blank" rel="noreferrer">
                  {link.label || link.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.status')}</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            style={{ maxWidth: 220 }}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(lang, s)}
              </option>
            ))}
          </select>
          <button className="btn" onClick={applyStatus} disabled={newStatus === task.status}>
            {t('common.save')}
          </button>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.comments')}</h3>
        {task.comments.length === 0 && <div className="muted">{t('common.noData')}</div>}
        {task.comments.map((c) => (
          <div key={c.id} className="comment">
            <div>{c.text}</div>
            <div className="when">{formatDateTime(c.created_at)}</div>
          </div>
        ))}
        <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
          <input
            placeholder={t('task.commentPlaceholder')}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addComment()}
          />
          <button className="btn" onClick={addComment}>
            {t('task.addComment')}
          </button>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.history')}</h3>
        {task.history.length === 0 && <div className="muted">{t('common.noData')}</div>}
        {task.history.map((h) => (
          <div key={h.id} className="history-row">
            <strong>{h.event_type}</strong>
            {h.field_name && <span className="muted"> · {h.field_name}</span>}
            {h.old_value && <span> ← {h.old_value}</span>}
            {h.new_value && <span> → {h.new_value}</span>}
            <span className="muted"> · {formatDateTime(h.created_at)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

