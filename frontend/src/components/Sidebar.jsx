import { NavLink } from 'react-router-dom';

export default function Sidebar({ title, links }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-portal-badge">{title}</div>
      {links.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            {Icon && <Icon size={18} />}
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </aside>
  );
}
