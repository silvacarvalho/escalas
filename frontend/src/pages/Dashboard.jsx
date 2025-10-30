import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Users, Church, Bell, TrendingUp, Activity } from 'lucide-react';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const storedUser = JSON.parse(localStorage.getItem('user'));
      setUser(storedUser);

      // Load notifications
      const notifResponse = await axios.get(`${API}/notifications`);
      setNotifications(notifResponse.data.slice(0, 5));

      // Load stats if pastor
      if (storedUser?.funcao === 'pastor_distrital' && storedUser?.id_distrito) {
        const statsResponse = await axios.get(`${API}/analytics/dashboard?id_distrito=${storedUser.id_distrito}`);
        setStats(statsResponse.data);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const acoesRapidas = [
    {
      titulo: 'Criar Escala',
      descricao: 'Gerar nova escala mensal',
      icon: Calendar,
      color: '#667eea',
      action: () => navigate('/schedules/create'),
      show: ['pastor_distrital', 'lider_igreja']
    },
    {
      titulo: 'Ver Escalas',
      descricao: 'Visualizar escalas existentes',
      icon: Activity,
      color: '#10b981',
      action: () => navigate('/schedules'),
      show: ['pastor_distrital', 'lider_igreja', 'pregador', 'cantor']
    },
    {
      titulo: 'Gerenciar Igrejas',
      descricao: 'Administrar igrejas do distrito',
      icon: Church,
      color: '#f59e0b',
      action: () => navigate('/churches'),
      show: ['pastor_distrital', 'lider_igreja']
    },
    {
      titulo: 'Gerenciar Usuários',
      descricao: 'Adicionar ou editar membros',
      icon: Users,
      color: '#ef4444',
      action: () => navigate('/users'),
      show: ['pastor_distrital', 'lider_igreja']
    },
    {
      titulo: 'Analytics',
      descricao: 'Ver métricas e relatórios',
      icon: TrendingUp,
      color: '#8b5cf6',
      action: () => navigate('/analytics'),
      show: ['pastor_distrital']
    },
  ];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="dashboard-container">
        {/* Welcome Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-8 text-white shadow-lg">
          <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Bem-vindo, {user?.nome_completo}!
          </h1>

          <p className="text-purple-100 text-lg">
            {user?.funcao === 'pastor_distrital' && 'Pastor Distrital'}
            {user?.funcao === 'lider_igreja' && 'Líder de Igreja'}
            {user?.funcao === 'pregador' && 'Pregador'}
            {user?.funcao === 'cantor' && 'Cantor'}
          </p>
        </div>

        {/* Cartões de Estatísticas - Somente para Pastor */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="shadow-md hover:shadow-lg transition-all">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Total de Igrejas</p>
                    <p className="text-3xl font-bold text-purple-600">{stats.total_igrejas}</p>
                  </div>
                  <Church className="h-12 w-12 text-purple-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="shadow-md hover:shadow-lg transition-all">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Pregadores Ativos</p>
                    <p className="text-3xl font-bold text-green-600">{stats.total_pregadores}</p>
                  </div>
                  <Users className="h-12 w-12 text-green-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="shadow-md hover:shadow-lg transition-all">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Cantores Ativos</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.total_cantores}</p>
                  </div>
                  <Users className="h-12 w-12 text-blue-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Ações Rápidas */}
        <div>
          <h2 className="text-2xl font-bold mb-4" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Ações Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {acoesRapidas
              .filter(action => action.show.includes(user?.funcao))
              .map((action, index) => {
                const Icon = action.icon;
                return (
                  <Card
                    key={index}
                    className="cursor-pointer hover:shadow-xl transition-all group"
                    onClick={action.action}
                    data-testid={`action-${action.titulo.toLowerCase().replace(/ /g, '-')}`}
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start space-x-4">
                        <div
                          className="p-3 rounded-xl"
                          style={{ backgroundColor: `${action.color}20` }}
                        >
                          <Icon style={{ color: action.color }} className="h-6 w-6" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg mb-1 group-hover:text-purple-600 transition-all">
                            {action.titulo}
                          </h3>
                          <p className="text-sm text-gray-500">{action.descricao}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        </div>

        {/* Notificações Recentes */}
        {notifications.length > 0 && (
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-purple-600" />
                <span>Notificações Recentes</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {notifications.map((notif, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border transition-all ${
                      notif.status === 'unread' ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200'
                    }`}
                    data-testid={`notification-${index}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-sm">{notif.titulo}</h4>
                        <p className="text-sm text-gray-600 mt-1">{notif.message}</p>
                      </div>
                      {notif.status === 'unread' && (
                        <span className="ml-2 h-2 w-2 bg-purple-600 rounded-full"></span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="ghost"
                className="w-full mt-4"
                onClick={() => navigate('/notifications')}
                data-testid="view-all-notifications-button"
              >
                Ver todas as notificações
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
