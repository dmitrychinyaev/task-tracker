import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useI18n } from '../i18n';
import type { PromptDraft } from '../types';
import { ErrorBanner, Loading } from '../components/ui';

const ROLES = [
  'General Development Task',
  'Frontend Developer',
  'Backend Developer',
  'Designer',
  'QA Engineer',
  'DevOps Engineer',
  'Analyst',
];

export default function PromptBuilderPage() {
  const { t } = useI18n();
  const [source, setSource] = useState('');
  const [role, setRole] = useState(ROLES[0]);
  const [title, setTitle] = useState('');
  const [links, setLinks] = useState('');
  const [context, setContext] = useState('');
  const [generated, setGenerated] = useState('');
  const [drafts, setDrafts] = useState<PromptDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const loadDrafts = useCallback(async () => {
    setError('');
    try {
      setDrafts(await api.listDrafts());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadDrafts();
      setLoading(false);
    })();
  }, [loadDrafts]);

  const generate = async () => {
    setError('');
    try {
      const res = await api.generatePrompt({
        source_text: source,
        role,
        title: title || null,
        links: links || null,
        context: context || null,
      });
      setGenerated(res.generated_prompt);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(generated);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError(t('common.error'));
    }
  };

  const saveDraft = async () => {
    setError('');
    try {
      await api.createDraft({
        source_text: source,
        role,
        title: title || null,
        links: links || null,
        context: context || null,
        generated_prompt: generated,
      });
      await loadDrafts();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const loadDraft = (d: PromptDraft) => {
    setSource(d.source_text);
    setRole(d.role);
    setTitle(d.title ?? '');
    setLinks(d.links ?? '');
    setContext(d.context ?? '');
    setGenerated(d.generated_prompt);
  };

  const removeDraft = async (d: PromptDraft) => {
    if (!window.confirm(t('common.confirmDelete'))) return;
    setError('');
    try {
      await api.deleteDraft(d.id);
      await loadDrafts();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">{t('prompts.title')}</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <div className="grid cols-2">
          <div className="field">
            <label>{t('prompts.role')}</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t('prompts.titleField')}</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label>{t('prompts.source')}</label>
          <textarea rows={5} value={source} onChange={(e) => setSource(e.target.value)} />
        </div>
        <div className="field">
          <label>{t('prompts.links')}</label>
          <textarea rows={2} value={links} onChange={(e) => setLinks(e.target.value)} />
        </div>
        <div className="field">
          <label>{t('prompts.context')}</label>
          <textarea rows={3} value={context} onChange={(e) => setContext(e.target.value)} />
        </div>
        <div className="form-actions" style={{ justifyContent: 'flex-start' }}>
          <button className="btn" onClick={generate}>
            {t('prompts.generate')}
          </button>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('prompts.generated')}</h3>
        <textarea className="mono" rows={10} value={generated} readOnly />
        <div className="form-actions" style={{ justifyContent: 'flex-start' }}>
          <button className="btn secondary" onClick={copy} disabled={!generated}>
            {copied ? t('common.copied') : t('common.copy')}
          </button>
          <button className="btn" onClick={saveDraft} disabled={!generated}>
            {t('prompts.saveDraft')}
          </button>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{t('prompts.drafts')}</h3>
        {drafts.length === 0 ? (
          <div className="muted">{t('prompts.noDrafts')}</div>
        ) : (
          drafts.map((d) => (
            <div key={d.id} className="comment">
              <div>
                <strong>{d.title || d.role}</strong>{' '}
                <span className="muted">· {d.role}</span>
              </div>
              <div className="muted" style={{ whiteSpace: 'pre-wrap' }}>
                {d.generated_prompt.slice(0, 160)}
                {d.generated_prompt.length > 160 ? '…' : ''}
              </div>
              <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                <button className="btn secondary small" onClick={() => loadDraft(d)}>
                  {t('common.edit')}
                </button>
                <button className="btn danger small" onClick={() => removeDraft(d)}>
                  {t('common.delete')}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

