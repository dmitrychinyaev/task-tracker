import { useNavigate } from 'react-router-dom';
import type { TaskSummary } from '../types';
import { useI18n } from '../i18n';
import { PriorityBadge, formatDeadline } from './ui';

export default function TaskCard({
  task,
  draggable = false,
  onDragStart,
}: {
  task: TaskSummary;
  draggable?: boolean;
  onDragStart?: (e: React.DragEvent, id: number) => void;
}) {
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <div
      className="task-card"
      draggable={draggable}
      onDragStart={(e) => onDragStart?.(e, task.id)}
      onClick={() => navigate(`/tasks/${task.id}`)}
    >
      <div className="title">{task.title}</div>
      <div className="meta">
        <span>{task.assignee?.name ?? t('task.noAssignee')}</span>
        {task.deadline && <span>· {formatDeadline(task.deadline)}</span>}
        {task.blocked_reason && <span title={task.blocked_reason}>⛔</span>}
      </div>
      <div className="meta" style={{ marginTop: 6, gap: 6 }}>
        <PriorityBadge priority={task.priority} />
        {task.tags.slice(0, 3).map((tag) => (
          <span key={tag.id} className="badge">
            {tag.name}
          </span>
        ))}
      </div>
    </div>
  );
}
