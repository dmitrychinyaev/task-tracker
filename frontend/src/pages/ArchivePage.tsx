import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { TaskSummary } from '../types';
import { ErrorBanner, Loading, StatusBadge, PriorityBadge, formatDateTime } from '../components/ui';

export default function ArchivePage() {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setTasks(await api.listTasks({ location: 'archive' }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('archive.title')}</h1>
      <ErrorBanner message={error} />

      {tasks.length === 0 ? (
        <div className="empty-hint">{t('archive.empty')}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('task.title')}</th>
              <th>{t('task.assignee')}</th>
              <th>{t('task.priority')}</th>
              <th>{t('task.completedAt')}</th>
              <th>{t('task.status')}</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>
                  <Link to={`/tasks/${task.id}`}>{task.title}</Link>
                </td>
                <td>{task.assignee?.name ?? t('task.noAssignee')}</td>
                <td>
                  <PriorityBadge priority={task.priority} />
                </td>
                <td>{formatDateTime(task.completed_at)}</td>
                <td>
                  <StatusBadge status={task.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
