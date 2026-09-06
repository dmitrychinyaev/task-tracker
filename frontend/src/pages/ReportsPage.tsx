import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { Sprint, TaskSummary } from '../types';
import { ErrorBanner, Loading } from '../components/ui';

export default function ReportsPage() {
  const { t } = useI18n();
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [sprintId, setSprintId] = useState('');
  const [taskId, setTaskId] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [s, tk] = await Promise.all([api.listSprints(), api.listTasks()]);
      setSprints(s);
      setTasks(tk);
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
      <h1 className="page-title">{t('reports.title')}</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('reports.kanban')}</h3>
        <a className="btn" href={api.kanbanReportUrl()}>
          {t('reports.generate')}
        </a>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('reports.activity')}</h3>
        <div className="grid cols-2">
          <div className="field">
            <label>{t('reports.activityStart')}</label>
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </div>
          <div className="field">
            <label>{t('reports.activityEnd')}</label>
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
        </div>
        <a className="btn" href={api.activityReportUrl(start || undefined, end || undefined)}>
          {t('reports.generate')}
        </a>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('reports.sprint')}</h3>
        <div className="field">
          <label>{t('reports.selectSprint')}</label>
          <select value={sprintId} onChange={(e) => setSprintId(e.target.value)}>
            <option value="">—</option>
            {sprints.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <a
          className="btn"
          href={sprintId ? api.sprintReportUrl(Number(sprintId)) : undefined}
          style={sprintId ? undefined : { pointerEvents: 'none', opacity: 0.5 }}
        >
          {t('reports.generate')}
        </a>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('reports.task')}</h3>
        <div className="field">
          <label>{t('task.title')}</label>
          <select value={taskId} onChange={(e) => setTaskId(e.target.value)}>
            <option value="">—</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                #{task.id} {task.title}
              </option>
            ))}
          </select>
        </div>
        <a
          className="btn"
          href={taskId ? api.taskReportUrl(Number(taskId)) : undefined}
          style={taskId ? undefined : { pointerEvents: 'none', opacity: 0.5 }}
        >
          {t('reports.generate')}
        </a>
      </div>
    </div>
  );
}
