import { Link, useLocation } from "react-router-dom";

export default function Navbar({ role, links }) {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/30 backdrop-blur-md border-b border-white/20 shadow-sm">
       <div className="max-w-7xl mx-auto px-6 lg:px-8 h-20 flex items-center justify-between">
          
          <div className="flex items-center gap-8 md:gap-12">
             {/* Profile Pic Placeholder */}
             <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/80 shadow-[0_2px_8px_rgba(0,0,0,0.2)] bg-gray-200 shrink-0">
                <img src="https://placehold.co/150x150/ebebeb/a3a3a3?text=User" alt="Profile" className="w-full h-full object-cover" />
             </div>

             {/* Links */}
             <div className="flex items-center gap-6 md:gap-8">
               {links.map((link) => {
                 // Active logic: check if the current path exactly matches or if it's the dashboard roots
                 const isActive = location.pathname === link.path || (link.path !== '/buyer' && link.path !== '/seller' && location.pathname.startsWith(link.path));
                 
                 return (
                   <Link 
                     key={link.path}
                     to={link.path}
                     className={`
                       text-white font-bold text-[1.1rem] font-inter transition-all duration-300 drop-shadow-[0_2px_4px_rgba(0,0,0,0.6)]
                       hover:text-[#D50000] hover:drop-shadow-none
                       ${isActive ? 'underline underline-offset-[6px] decoration-[3px] decoration-white hover:decoration-[#D50000]' : ''}
                     `}
                   >
                     {link.label}
                   </Link>
                 )
               })}
             </div>
          </div>

          <div className="hidden sm:flex items-center">
             <span className="text-white font-bold drop-shadow-[0_2px_4px_rgba(0,0,0,0.6)] uppercase text-xs tracking-widest opacity-90">
               {role}
             </span>
          </div>

       </div>
    </nav>
  );
}
