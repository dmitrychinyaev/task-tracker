import { NavLink, Outlet } from 'react-router-dom';
import { useI18n } from '../i18n';

export default function Layout() {
  const { t, lang, setLang } = useI18n();

  const nav = [
    { to: '/inbox', label: t('nav.inbox') },
    { to: '/backlog', label: t('nav.backlog') },
    { to: '/board', label: t('nav.board') },
    { to: '/archive', label: t('nav.archive') },
    { to: '/assignees', label: t('nav.assignees') },
    { to: '/sprints', label: t('nav.sprints') },
    { to: '/reports', label: t('nav.reports') },
    { to: '/prompts', label: t('nav.prompts') },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">{t('app.title')}</div>
        {nav.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            {n.label}
          </NavLink>
        ))}
        <div className="lang-switcher" title={t('common.language')}>
          <button className={lang === 'ru' ? 'active' : ''} onClick={() => setLang('ru')}>
            RU
          </button>
          <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>
            EN
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
