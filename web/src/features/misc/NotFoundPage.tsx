import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/Card';

export default function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <Card className="not-found">
      <h1 className="mono">{t('notFound.title')}</h1>
      <p>{t('notFound.text')}</p>
      <Link to="/map" className="btn btn-primary">{t('notFound.home')}</Link>
    </Card>
  );
}
