import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useI18n, sprintStatusLabel } from '../i18n';
import type { Sprint } from '../types';
import { ErrorBanner, Loading, Modal, formatDate } from '../components/ui';

const SPRINT_STATUSES = ['planned', 'active', 'completed', 'cancelled'];

export default function SprintsPage() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState<Sprint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Sprint | null>(null);
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [status, setStatus] = useState('planned');
  const [description, setDescription] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setItems(await api.listSprints());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    setEditing(null);
    setName('');
    setStart('');
    setEnd('');
    setStatus('planned');
    setDescription('');
    setShowForm(true);
  };

  const openEdit = (s: Sprint) => {
    setEditing(s);
    setName(s.name);
    setStart(s.start_date);
    setEnd(s.end_date);
    setStatus(s.status);
    setDescription(s.description ?? '');
    setShowForm(true);
  };

  const save = async () => {
    setError('');
    try {
      const payload = {
        name,
        start_date: start,
        end_date: end,
        status,
        description: description || null,
      };
      if (editing) await api.updateSprint(editing.id, payload);
      else await api.createSprint(payload);
      setShowForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const remove = async (s: Sprint) => {
    if (!window.confirm(t('common.confirmDelete'))) return;
    setError('');
    try {
      await api.deleteSprint(s.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('sprints.title')}</h1>
      <ErrorBanner message={error} />
      <div className="toolbar">
        <button className="btn" onClick={openCreate}>
          {t('sprints.new')}
        </button>
      </div>

      {items.length === 0 ? (
        <div className="empty-hint">{t('sprints.empty')}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('sprints.name')}</th>
              <th>{t('sprints.start')}</th>
              <th>{t('sprints.end')}</th>
              <th>{t('sprints.status')}</th>
              <th>{t('sprints.description')}</th>
              <th>{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{formatDate(s.start_date)}</td>
                <td>{formatDate(s.end_date)}</td>
                <td>{sprintStatusLabel(lang, s.status)}</td>
                <td>{s.description ?? '—'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn secondary small" onClick={() => openEdit(s)}>
                      {t('common.edit')}
                    </button>
                    <button className="btn danger small" onClick={() => remove(s)}>
                      {t('common.delete')}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showForm && (
        <Modal
          title={editing ? t('common.edit') : t('sprints.new')}
          onClose={() => setShowForm(false)}
        >
          <div className="field">
            <label>{t('sprints.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="grid cols-2">
            <div className="field">
              <label>{t('sprints.start')}</label>
              <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
            <div className="field">
              <label>{t('sprints.end')}</label>
              <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label>{t('sprints.status')}</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {SPRINT_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {sprintStatusLabel(lang, s)}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t('sprints.description')}</label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="form-actions">
            <button className="btn secondary" onClick={() => setShowForm(false)}>
              {t('common.cancel')}
            </button>
            <button className="btn" onClick={save}>
              {t('common.save')}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
