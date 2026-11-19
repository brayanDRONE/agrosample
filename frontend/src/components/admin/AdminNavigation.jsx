import { Link } from 'react-router-dom';
import './AdminNavigation.css';

function LeafIcon() {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M27.5 4.5C16 4.5 8.5 9.2 7.1 17.1c-.6 3.2.7 5.7 3.3 6.2 3.2.6 6.1-1.6 7.6-5.3 1.5-3.6 4.3-7.7 9.5-13.5Z" fill="currentColor" />
      <path d="M5 27c4.2-5.7 8.6-8.6 14.4-10.7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function AdminBrand() {
  return <div className="admin-brand"><LeafIcon /><span>Agro<strong>Sample</strong></span></div>;
}

export default function AdminNavigation({ current }) {
  return (
    <nav className="admin-sidebar" aria-label="Navegación de administración">
      <Link to="/admin" className="admin-sidebar-brand" aria-label="Panel de administración"><LeafIcon /></Link>
      <div className="admin-sidebar-links">
        <Link to="/admin" className={`admin-sidebar-link${current === 'dashboard' ? ' active' : ''}`} aria-label="Panel de administración" aria-current={current === 'dashboard' ? 'page' : undefined} title="Panel de administración">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="m3 11 9-7 9 7M5 10v10h14V10M9 20v-6h6v6" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </Link>
        <Link to="/admin/establishments" className={`admin-sidebar-link${current === 'establishments' ? ' active' : ''}`} aria-label="Establecimientos" aria-current={current === 'establishments' ? 'page' : undefined} title="Establecimientos">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M5 21V4h11v17M16 10h3v11M3 21h18M9 8h3M9 12h3M9 16h3" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </Link>
        <Link to="/admin/perfil" className={`admin-sidebar-link${current === 'profile' ? ' active' : ''}`} aria-label="Perfil de administrador" aria-current={current === 'profile' ? 'page' : undefined} title="Perfil de administrador">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" strokeLinecap="round" /></svg>
        </Link>
      </div>
    </nav>
  );
}
