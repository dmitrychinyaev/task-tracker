import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, imageUrl } from '../api';
import { useI18n } from '../i18n';
import type { Assignee, DescriptionBlock, Sprint, Tag, TaskLinkIn } from '../types';
import { ErrorBanner, Loading } from '../components/ui';

export default function TaskFormPage() {
  const { id } = useParams();
  const editId = id ? Number(id) : null;
  const { t } = useI18n();
  const navigate = useNavigate();

  const [assignees, setAssignees] = useState<Assignee[]>([]);
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [title, setTitle] = useState('');
  const [assigneeId, setAssigneeId] = useState('');
  const [priority, setPriority] = useState('');
  const [sprintId, setSprintId] = useState('');
  const [deadline, setDeadline] = useState('');
  const [tagIds, setTagIds] = useState<number[]>([]);
  const [blocks, setBlocks] = useState<DescriptionBlock[]>([]);
  const [links, setLinks] = useState<TaskLinkIn[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadRefs = useCallback(async () => {
    const [a, s, tg] = await Promise.all([
      api.listAssignees(),
      api.listSprints(),
      api.listTags(),
    ]);
    setAssignees(a);
    setSprints(s);
    setTags(tg);
    if (a.length > 0 && !editId) setAssigneeId(String(a[0].id));
  }, [editId]);

  const loadTask = useCallback(async () => {
    if (!editId) return;
    const task = await api.getTask(editId);
    setTitle(task.title);
    setAssigneeId(task.assignee_id ? String(task.assignee_id) : '');
    setPriority(task.priority ?? '');
    setSprintId(task.sprint_id ? String(task.sprint_id) : '');
    setDeadline(task.deadline ?? '');
    setTagIds(task.tags.map((x) => x.id));
    setBlocks(task.description);
    setLinks(task.links.map((l) => ({ label: l.label, url: l.url })));
  }, [editId]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError('');
      try {
        await loadRefs();
        await loadTask();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [loadRefs, loadTask]);

  const addTextBlock = () => setBlocks([...blocks, { type: 'text', content: '' }]);
  const updateTextBlock = (i: number, content: string) =>
    setBlocks(blocks.map((b, idx) => (idx === i ? { type: 'text', content } : b)));
  const removeBlock = (i: number) => setBlocks(blocks.filter((_, idx) => idx !== i));

  const uploadImage = async (file: File) => {
    setError('');
    try {
      const meta = await api.uploadImage(file);
      setBlocks([...blocks, { type: 'image', image_id: meta.id }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const addLink = () => setLinks([...links, { label: '', url: '' }]);
  const updateLink = (i: number, patch: Partial<TaskLinkIn>) =>
    setLinks(links.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));
  const removeLink = (i: number) => setLinks(links.filter((_, idx) => idx !== i));

  const toggleTag = (tagId: number) =>
    setTagIds(tagIds.includes(tagId) ? tagIds.filter((x) => x !== tagId) : [...tagIds, tagId]);

  const save = async () => {
    if (!title.trim()) {
      setError(t('task.title') + ': required');
      return;
    }
    if (!editId && !assigneeId) {
      setError(t('task.assignee') + ': required');
      return;
    }
    setError('');
    try {
      const base = {
        title: title.trim(),
        priority: (priority || null) as 'low' | 'medium' | 'high' | 'critical' | null,
        sprint_id: sprintId ? Number(sprintId) : null,
        deadline: deadline || null,
        tag_ids: tagIds,
        description: blocks,
        links: links
          .filter((l) => l.url.trim())
          .map((l) => ({ label: l.label?.trim() || null, url: l.url.trim() })),
      };
      const task = editId
        ? await api.updateTask(editId, {
            ...base,
            assignee_id: assigneeId ? Number(assigneeId) : null,
          })
        : await api.createTask({ ...base, assignee_id: Number(assigneeId) });
      navigate(`/tasks/${task.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{editId ? t('task.edit') : t('task.new')}</h1>
      <ErrorBanner message={error} />

      {assignees.length === 0 && (
        <div className="error-banner">
          <Link to="/assignees">{t('assignees.new')}</Link> — {t('task.assignee')}
        </div>
      )}

      <div className="card">
        <div className="field">
          <label>{t('task.title')}</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>

        <div className="grid cols-2">
          <div className="field">
            <label>{t('task.assignee')}</label>
            <select value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}>
              <option value="">—</option>
              {assignees.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t('task.priority')}</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="">—</option>
              {['low', 'medium', 'high', 'critical'].map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t('task.sprint')}</label>
            <select value={sprintId} onChange={(e) => setSprintId(e.target.value)}>
              <option value="">—</option>
              {sprints.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t('task.deadline')}</label>
            <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
          </div>
        </div>

        <div className="field">
          <label>{t('task.tags')}</label>
          <div className="tag-list">
            {tags.map((tg) => (
              <span
                key={tg.id}
                className="tag-pill"
                style={{ cursor: 'pointer', opacity: tagIds.includes(tg.id) ? 1 : 0.5 }}
                onClick={() => toggleTag(tg.id)}
              >
                {tg.name}
              </span>
            ))}
            {tags.length === 0 && <span className="muted">{t('common.noData')}</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.description')}</h3>
        {blocks.map((block, i) => (
          <div key={i} className="description-block">
            {block.type === 'text' ? (
              <textarea
                rows={3}
                value={block.content}
                placeholder={t('task.textBlockPlaceholder')}
                onChange={(e) => updateTextBlock(i, e.target.value)}
              />
            ) : (
              <img src={imageUrl(block.image_id)} alt="" />
            )}
            <button className="btn danger small" onClick={() => removeBlock(i)}>
              ×
            </button>
          </div>
        ))}
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn secondary small" onClick={addTextBlock}>
            {t('task.addTextBlock')}
          </button>
          <button className="btn secondary small" onClick={() => fileRef.current?.click()}>
            {t('task.addImageBlock')}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void uploadImage(f);
              e.target.value = '';
            }}
          />
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('task.links')}</h3>
        {links.map((link, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              placeholder={t('task.linkLabel')}
              value={link.label ?? ''}
              onChange={(e) => updateLink(i, { label: e.target.value })}
              style={{ maxWidth: 180 }}
            />
            <input
              placeholder={t('task.linkUrl')}
              value={link.url}
              onChange={(e) => updateLink(i, { url: e.target.value })}
            />
            <button className="btn danger small" onClick={() => removeLink(i)}>
              ×
            </button>
          </div>
        ))}
        <button className="btn secondary small" onClick={addLink}>
          {t('task.addLink')}
        </button>
      </div>

      <div className="form-actions">
        <button className="btn secondary" onClick={() => navigate(-1)}>
          {t('common.cancel')}
        </button>
        <button className="btn" onClick={save}>
          {t('common.save')}
        </button>
      </div>
    </div>
  );
}

