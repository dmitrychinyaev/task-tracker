import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { Assignee } from '../types';
import { ErrorBanner, Loading, Modal } from '../components/ui';

const ROLES = ['Frontend Developer', 'Backend Developer', 'Designer', 'Analyst', 'QA', 'Other'];

export default function AssigneesPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<Assignee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<Assignee | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [note, setNote] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setItems(await api.listAssignees());
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
    setRole('');
    setNote('');
    setShowForm(true);
  };

  const openEdit = (a: Assignee) => {
    setEditing(a);
    setName(a.name);
    setRole(a.role ?? '');
    setNote(a.note ?? '');
    setShowForm(true);
  };

  const save = async () => {
    setError('');
    try {
      const payload = { name, role: role || null, note: note || null };
      if (editing) await api.updateAssignee(editing.id, payload);
      else await api.createAssignee(payload);
      setShowForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const remove = async (a: Assignee) => {
    if (!window.confirm(t('common.confirmDelete'))) return;
    setError('');
    try {
      await api.deleteAssignee(a.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('assignees.title')}</h1>
      <ErrorBanner message={error} />
      <div className="toolbar">
        <button className="btn" onClick={openCreate}>
          {t('assignees.new')}
        </button>
      </div>

      {items.length === 0 ? (
        <div className="empty-hint">{t('assignees.empty')}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('assignees.name')}</th>
              <th>{t('assignees.role')}</th>
              <th>{t('assignees.note')}</th>
              <th>{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td>{a.role ?? '—'}</td>
                <td>{a.note ?? '—'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn secondary small" onClick={() => openEdit(a)}>
                      {t('common.edit')}
                    </button>
                    <button className="btn danger small" onClick={() => remove(a)}>
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
          title={editing ? t('common.edit') : t('assignees.new')}
          onClose={() => setShowForm(false)}
        >
          <div className="field">
            <label>{t('assignees.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="field">
            <label>{t('assignees.role')}</label>
            <input list="roles" value={role} onChange={(e) => setRole(e.target.value)} />
            <datalist id="roles">
              {ROLES.map((r) => (
                <option key={r} value={r} />
              ))}
            </datalist>
          </div>
          <div className="field">
            <label>{t('assignees.note')}</label>
            <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
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
