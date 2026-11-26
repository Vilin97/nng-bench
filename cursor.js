// Visible cursor overlay: follows the real mouse events Chrome receives from the agent's
// automation (which never moves an OS pointer), plus a red ripple on every click.
(() => {
  if (window.__agentCursor) return; window.__agentCursor = true;
  let c, x = 720, y = 450;
  const ensure = () => {
    if (c && c.isConnected) return c;
    if (!document.documentElement) return null;
    c = document.createElement('div');
    c.setAttribute('aria-hidden', 'true');
    c.innerHTML = '<svg width="26" height="34" viewBox="0 0 26 34"><path d="M3 2 L3 27 L9 21 L13.5 31 L18 29 L13.5 19 L22 19 Z" fill="white" stroke="black" stroke-width="2" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, { position: 'fixed', left: '0', top: '0', width: '26px', height: '34px', zIndex: '2147483647',
      pointerEvents: 'none', transition: 'transform 0.3s ease-out', filter: 'drop-shadow(1px 2px 2px rgba(0,0,0,.45))',
      transform: `translate(${x - 3}px, ${y - 2}px)` });
    document.documentElement.appendChild(c);
    return c;
  };
  const move = e => { x = e.clientX; y = e.clientY; const el = ensure(); if (el) el.style.transform = `translate(${x - 3}px, ${y - 2}px)`; };
  addEventListener('mousemove', move, true);
  addEventListener('mousedown', e => {
    move(e);
    const r = document.createElement('div');
    r.setAttribute('aria-hidden', 'true');
    Object.assign(r.style, { position: 'fixed', left: e.clientX - 16 + 'px', top: e.clientY - 16 + 'px', width: '32px', height: '32px',
      borderRadius: '50%', border: '3px solid #e53935', background: 'rgba(229,57,53,.25)', zIndex: '2147483646',
      pointerEvents: 'none', transition: 'transform .6s ease-out, opacity .6s ease-out' });
    document.documentElement.appendChild(r);
    requestAnimationFrame(() => requestAnimationFrame(() => { r.style.transform = 'scale(2.2)'; r.style.opacity = '0'; }));
    setTimeout(() => r.remove(), 700);
  }, true);
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', ensure); else ensure();
})();
