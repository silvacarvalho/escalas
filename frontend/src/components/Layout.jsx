import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Home,
  Calendar,
  Church,
  Users,
  Bell,
  User,
  LogOut,
  BarChart3,
  Menu,
  X,
  MapPin
} from 'lucide-react';

export default function Layout({ children }) {
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const menuItems = [
    {
      title: 'Início',
      icon: Home,
      path: '/',
      show: ['pastor_distrital', 'lider_igreja', 'pregador', 'cantor']
    },
    {
      title: 'Distritos',
      icon: MapPin,
      path: '/districts',
      show: ['pastor_distrital']
    },
    {
      title: 'Igrejas',
      icon: Church,
      path: '/churches',
      show: ['pastor_distrital', 'lider_igreja']
    },
    {
      title: 'Usuários',
      icon: Users,
      path: '/users',
      show: ['pastor_distrital', 'lider_igreja']
    },
    {
      title: 'Escalas',
      icon: Calendar,
      path: '/schedules',
      show: ['pastor_distrital', 'lider_igreja', 'pregador', 'cantor']
    },
    {
      title: 'Analytics',
      icon: BarChart3,
      path: '/analytics',
      show: ['pastor_distrital']
    },
    {
      title: 'Notificações',
      icon: Bell,
      path: '/notifications',
      show: ['pastor_distrital', 'lider_igreja', 'pregador', 'cantor']
    },
    {
      title: 'Perfil',
      icon: User,
      path: '/profile',
      show: ['pastor_distrital', 'lider_igreja', 'pregador', 'cantor']
    },
  ];

  const filteredMenuItems = menuItems.filter(item => 
    item.show.includes(user?.role)
  );

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b">
        <h2 className="text-2xl font-bold" style={{
          fontFamily: 'Space Grotesk, sans-serif',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>Sistema de Escalas</h2>
      </div>
      
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {filteredMenuItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={index}
                variant={isActive ? 'default' : 'ghost'}
                className={`w-full justify-start text-left h-12 ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700'
                    : 'hover:bg-purple-50'
                }`}
                onClick={() => {
                  navigate(item.path);
                  setSidebarOpen(false);
                }}
                data-testid={`nav-${item.title.toLowerCase()}`}
              >
                <Icon className="mr-3 h-5 w-5" />
                {item.title}
              </Button>
            );
          })}
        </nav>
      </ScrollArea>

      <div className="p-4 border-t">
        <div className="flex items-center space-x-3 mb-3 p-3 bg-gray-50 rounded-lg">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="outline"
          className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700 border-red-200"
          onClick={handleLogout}
          data-testid="logout-button"
        >
          <LogOut className="mr-3 h-5 w-5" />
          Sair
        </Button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:flex-col md:w-64 bg-white border-r shadow-sm">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white z-50 md:hidden shadow-xl">
            <SidebarContent />
          </aside>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden bg-white border-b p-4 flex items-center justify-between shadow-sm">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            data-testid="mobile-menu-button"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
          <h1 className="text-lg font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Sistema de Escalas</h1>
          <div className="w-10" /> {/* Spacer */}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-4 md:p-6 lg:p-8 max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
