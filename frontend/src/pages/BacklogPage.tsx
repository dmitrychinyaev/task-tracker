import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useI18n, statusLabel } from '../i18n';
import type { TaskSummary } from '../types';
import { ErrorBanner, Loading, StatusBadge, PriorityBadge, formatDeadline } from '../components/ui';

const BOARD_STATUSES = ['backlog', 'todo', 'in_progress', 'review', 'qa', 'blocked'];

export default function BacklogPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [targetStatus, setTargetStatus] = useState<Record<number, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setTasks(await api.listTasks({ location: 'backlog' }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = tasks.filter((task) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      task.title.toLowerCase().includes(q) ||
      (task.assignee?.name ?? '').toLowerCase().includes(q)
    );
  });

  const statusFor = (id: number) => targetStatus[id] ?? 'todo';

  const moveToBoard = async (id: number) => {
    setError('');
    try {
      await api.addToBoard(id, statusFor(id));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('backlog.title')}</h1>
      <ErrorBanner message={error} />

      <div className="toolbar">
        <input
          placeholder={t('common.search')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 280 }}
        />
        <button className="btn" onClick={() => navigate('/tasks/new')}>
          {t('backlog.new')}
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-hint">{t('backlog.empty')}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('task.title')}</th>
              <th>{t('task.assignee')}</th>
              <th>{t('task.priority')}</th>
              <th>{t('task.deadline')}</th>
              <th>{t('task.status')}</th>
              <th>{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((task) => (
              <tr key={task.id}>
                <td>
                  <Link to={`/tasks/${task.id}`}>{task.title}</Link>
                </td>
                <td>{task.assignee?.name ?? t('task.noAssignee')}</td>
                <td>
                  <PriorityBadge priority={task.priority} />
                </td>
                <td>{formatDeadline(task.deadline) || '—'}</td>
                <td>
                  <StatusBadge status={task.status} />
                </td>
                <td>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <select
                      value={statusFor(task.id)}
                      onChange={(e) =>
                        setTargetStatus((s) => ({ ...s, [task.id]: e.target.value }))
                      }
                      style={{ width: 150 }}
                    >
                      {BOARD_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {statusLabel(lang, s)}
                        </option>
                      ))}
                    </select>
                    <button className="btn small" onClick={() => moveToBoard(task.id)}>
                      {t('backlog.moveToBoard')}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
