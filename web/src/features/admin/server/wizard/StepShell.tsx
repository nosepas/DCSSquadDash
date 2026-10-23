import type { ReactNode } from 'react';

interface Props {
  n: number;
  id: string;
  title: string;
  help: string;
  children: ReactNode;
}

/** One numbered step: heading, a plain-language help line, then the content. */
export function StepShell({ n, id, title, help, children }: Props) {
  return (
    <li className="wizard-step" aria-labelledby={`${id}-title`}>
      <span className="wizard-num" aria-hidden="true">{n}</span>
      <div className="wizard-body">
        <h3 id={`${id}-title`} className="wizard-step-title">{title}</h3>
        <p className="muted wizard-help">{help}</p>
        {children}
      </div>
    </li>
  );
}
