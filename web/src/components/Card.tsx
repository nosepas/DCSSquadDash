import type { ReactNode } from 'react';

interface Props {
  title?: string;
  actions?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function Card({ title, actions, className = '', children }: Props) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          {title && <h2 className="card-title">{title}</h2>}
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="page-head">
      <h1>{title}</h1>
      {children}
    </div>
  );
}
