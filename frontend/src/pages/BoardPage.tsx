import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useI18n, statusLabel } from '../i18n';
import type { TaskSummary } from '../types';
import { ErrorBanner, Loading } from '../components/ui';
import TaskCard from '../components/TaskCard';

const COLUMNS = ['backlog', 'todo', 'in_progress', 'review', 'qa', 'blocked', 'done'];

export default function BoardPage() {
  const { t, lang } = useI18n();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [overCol, setOverCol] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setTasks(await api.listTasks({ location: 'board' }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const move = async (id: number, status: string) => {
    setError('');
    try {
      if (status === 'blocked') {
        const reason = window.prompt(t('board.blockReasonPrompt'));
        if (reason === null) return;
        await api.moveTask(id, status, reason);
      } else {
        await api.moveTask(id, status);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDrop = (status: string) => {
    setOverCol(null);
    if (draggingId === null) return;
    void move(draggingId, status);
    setDraggingId(null);
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('board.title')}</h1>
      <ErrorBanner message={error} />

      <div className="toolbar">
        <Link className="btn secondary" to="/backlog">
          {t('board.backlogHint')}
        </Link>
        <Link className="btn" to="/tasks/new">
          {t('backlog.new')}
        </Link>
      </div>

      <div className="board">
        {COLUMNS.map((col) => {
          const colTasks = tasks.filter((task) => task.status === col);
          return (
            <div
              key={col}
              className={`board-col ${overCol === col ? 'drop-target' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setOverCol(col);
              }}
              onDragLeave={() => setOverCol((c) => (c === col ? null : c))}
              onDrop={() => handleDrop(col)}
            >
              <div className="board-col-header">
                <span>{statusLabel(lang, col)}</span>
                <span className="count">{colTasks.length}</span>
              </div>
              <div className="board-col-body">
                {colTasks.map((task) => (
                  <div
                    key={task.id}
                    className={draggingId === task.id ? 'dragging' : ''}
                  >
                    <TaskCard
                      task={task}
                      draggable
                      onDragStart={(e) => {
                        e.dataTransfer.effectAllowed = 'move';
                        setDraggingId(task.id);
                      }}
                    />
                  </div>
                ))}
                {colTasks.length === 0 && col === 'done' && (
                  <div className="empty-hint">{t('board.doneHint')}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
