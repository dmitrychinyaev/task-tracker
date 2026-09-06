import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { TaskSummary } from '../types';
import { ErrorBanner, Loading, formatDateTime } from '../components/ui';

function senderOf(task: TaskSummary, fallback: string): string {
  const meta = task.telegram_metadata as Record<string, unknown> | null | undefined;
  if (meta?.sender_name) return String(meta.sender_name);
  if (meta?.sender_user_id) return `ID ${meta.sender_user_id}`;
  return fallback;
}

export default function InboxPage() {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setTasks(await api.listTasks({ location: 'inbox' }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const moveToBacklog = async (id: number) => {
    setError('');
    try {
      await api.moveToBacklog(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('inbox.title')}</h1>
      <ErrorBanner message={error} />

      {tasks.length === 0 ? (
        <div className="empty-hint">{t('inbox.empty')}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('task.title')}</th>
              <th>{t('inbox.sender')}</th>
              <th>{t('inbox.receivedAt')}</th>
              <th>{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>
                  <Link to={`/tasks/${task.id}`}>{task.title}</Link>
                </td>
                <td>{senderOf(task, t('task.noAssignee'))}</td>
                <td>
                  {formatDateTime(
                    (task.telegram_metadata?.received_at as string | undefined) ?? task.created_at,
                  )}
                </td>
                <td>
                  <button className="btn small" onClick={() => moveToBacklog(task.id)}>
                    {t('inbox.moveToBacklog')}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
