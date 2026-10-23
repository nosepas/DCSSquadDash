/** DOM nodes for Leaflet content: Leaflet writes strings with innerHTML, so server-provided text is always passed as a node. */
export function textNode(text: string, tag: 'span' | 'b' | 'strong' | 'div' = 'span', className?: string): HTMLElement {
  const el = document.createElement(tag);
  if (className) el.className = className;
  el.textContent = text;
  return el;
}

/** Tooltip body for a marker: a single text-only element. */
export function labelNode(text: string): HTMLElement {
  return textNode(text);
}
