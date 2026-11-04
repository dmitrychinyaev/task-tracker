import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { Assignee, Role } from '../types';
import { ErrorBanner, Loading, Modal } from '../components/ui';

type Tab = 'staff' | 'roles';

function EditIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="M19 6l-1 14H6L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
  );
}

export default function AssigneesPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<Tab>('staff');
  const [items, setItems] = useState<Assignee[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [editing, setEditing] = useState<Assignee | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [roleId, setRoleId] = useState('');
  const [note, setNote] = useState('');

  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [showRoleForm, setShowRoleForm] = useState(false);
  const [roleName, setRoleName] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [assignees, roleList] = await Promise.all([api.listAssignees(), api.listRoles()]);
      setItems(assignees);
      setRoles(roleList);
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
    setRoleId('');
    setNote('');
    setShowForm(true);
  };

  const openEdit = (a: Assignee) => {
    setEditing(a);
    setName(a.name);
    setRoleId(a.role ? String(a.role.id) : '');
    setNote(a.note ?? '');
    setShowForm(true);
  };

  const save = async () => {
    setError('');
    try {
      const payload = { name, role_id: roleId ? Number(roleId) : null, note: note || null };
      if (editing) await api.updateAssignee(editing.id, payload);
      else await api.createAssignee(payload);
      setShowForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const openRoleCreate = () => {
    setEditingRole(null);
    setRoleName('');
    setShowRoleForm(true);
  };

  const openRoleEdit = (r: Role) => {
    setEditingRole(r);
    setRoleName(r.name);
    setShowRoleForm(true);
  };

  const saveRole = async () => {
    setError('');
    try {
      if (editingRole) await api.updateRole(editingRole.id, { name: roleName.trim() });
      else await api.createRole({ name: roleName.trim() });
      setShowRoleForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const removeRole = async (r: Role) => {
    if (!window.confirm(t('common.confirmDelete'))) return;
    setError('');
    try {
      await api.deleteRole(r.id);
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

      <div className="tabs">
        <button className={tab === 'staff' ? 'tab active' : 'tab'} onClick={() => setTab('staff')}>
          {t('assignees.tabStaff')}
        </button>
        <button className={tab === 'roles' ? 'tab active' : 'tab'} onClick={() => setTab('roles')}>
          {t('assignees.tabRoles')}
        </button>
      </div>

      {tab === 'staff' ? (
        <>
          <div className="toolbar">
            <button className="btn" onClick={openCreate}>
              {t('assignees.new')}
            </button>
          </div>

          {items.length === 0 ? (
            <div className="empty-hint">{t('assignees.empty')}</div>
          ) : (
            <div className="table-wrap">
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
                      <td>{a.role?.name ?? '—'}</td>
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
            </div>
          )}
        </>
      ) : (
        <>
          <div className="toolbar">
            <button className="btn" onClick={openRoleCreate}>
              {t('roles.new')}
            </button>
          </div>

          {roles.length === 0 ? (
            <div className="empty-hint">{t('roles.empty')}</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{t('roles.name')}</th>
                    <th>{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {roles.map((r) => (
                    <tr key={r.id}>
                      <td>{r.name}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn secondary small icon-btn"
                            title={t('common.edit')}
                            aria-label={t('common.edit')}
                            onClick={() => openRoleEdit(r)}
                          >
                            <EditIcon />
                          </button>
                          <button
                            className="btn danger small icon-btn"
                            title={t('common.delete')}
                            aria-label={t('common.delete')}
                            onClick={() => removeRole(r)}
                          >
                            <TrashIcon />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
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
            <select value={roleId} onChange={(e) => setRoleId(e.target.value)}>
              <option value="">{t('assignees.noRole')}</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
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

      {showRoleForm && (
        <Modal
          title={editingRole ? t('common.edit') : t('roles.new')}
          onClose={() => setShowRoleForm(false)}
        >
          <div className="field">
            <label>{t('roles.name')}</label>
            <input value={roleName} onChange={(e) => setRoleName(e.target.value)} />
          </div>
          <div className="form-actions">
            <button className="btn secondary" onClick={() => setShowRoleForm(false)}>
              {t('common.cancel')}
            </button>
            <button className="btn" onClick={saveRole} disabled={!roleName.trim()}>
              {t('common.save')}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
