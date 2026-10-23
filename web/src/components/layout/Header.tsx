import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LanguageSelect } from './LanguageSelect';
import { Nav } from './Nav';
import { ServerSelect } from './ServerSelect';
import { UserMenu } from './UserMenu';

export function Header() {
  const { t } = useTranslation();
  return (
    <header className="app-header">
      <a href="#main" className="skip-link">
        {t('header.skip')}
      </a>
      <div className="header-row">
        <Link to="/map" className="brand" aria-label="FOX3">
          <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
            <path d="M16 3l11 24-11-6.5L5 27z" fill="currentColor" />
          </svg>
          <span className="brand-text">FOX3</span>
        </Link>
        <div className="header-tools">
          <ServerSelect />
          <LanguageSelect />
          <UserMenu />
        </div>
      </div>
      <Nav />
    </header>
  );
}
