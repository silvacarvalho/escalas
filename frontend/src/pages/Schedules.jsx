import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar as CalendarIcon, Eye, Trash2, Plus } from 'lucide-react';
import { toast } from 'sonner';

export default function Schedules() {
  const [schedules, setSchedules] = useState([]);
  const [churches, setChurches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem('user'));
    setUser(storedUser);
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [schedulesRes, churchesRes] = await Promise.all([
        axios.get(`${API}/schedules`),
        axios.get(`${API}/churches`)
      ]);
      setSchedules(schedulesRes.data);
      setChurches(churchesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar escalas');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta escala?')) return;
    try {
      await axios.delete(`${API}/schedules/${id}`);
      toast.success('Escala excluída com sucesso!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir escala');
    }
  };

  const getMonthName = (month) => {
    const months = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    return months[month - 1];
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'confirmed':
        return 'bg-blue-100 text-blue-800';
      case 'active':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'draft':
        return 'Rascunho';
      case 'confirmed':
        return 'Confirmada';
      case 'active':
        return 'Ativa';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </Layout>
    );
  }

  const canManage = user?.funcao === 'pastor_distrital' || user?.funcao === 'lider_igreja';

  return (
    <Layout>
      <div className="space-y-6" data-testid="schedules-container">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Escalas</h1>
          {canManage && (
            <Button
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
              onClick={() => navigate('/schedules/create')}
              data-testid="create-schedule-button"
            >
              <Plus className="mr-2 h-4 w-4" />
              Nova Escala
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {schedules.map((schedule) => {
            const church = churches.find(c => c.id === schedule.id_igreja);
            const filledItems = schedule.items?.filter(item => item.id_pregador).length || 0;
            const totalItems = schedule.items?.length || 0;
            const completionRate = totalItems > 0 ? Math.round((filledItems / totalItems) * 100) : 0;

            return (
              <Card key={schedule.id} className="hover:shadow-lg transition-all" data-testid={`schedule-card-${schedule.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center space-x-2 mb-2">
                        <CalendarIcon className="h-5 w-5 text-purple-600" />
                        <span>{getMonthName(schedule.mes)} de {schedule.ano}</span>
                      </CardTitle>
                      <p className="text-sm text-gray-600 font-medium">{church?.nome || 'Igreja não encontrada'}</p>
                    </div>
                    <Badge className={getStatusColor(schedule.status)}>
                      {getStatusLabel(schedule.status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Preenchimento</span>
                        <span className="font-semibold">{completionRate}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all"
                          style={{ width: `${completionRate}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {filledItems} de {totalItems} cultos preenchidos
                      </p>
                    </div>

                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => navigate(`/schedules/${schedule.id}/calendar`)}
                        data-testid={`view-schedule-${schedule.id}`}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Visualizar
                      </Button>
                      {canManage && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:bg-red-50"
                          onClick={() => handleDelete(schedule.id)}
                          data-testid={`delete-schedule-${schedule.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {schedules.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <CalendarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Nenhuma escala cadastrada</p>
              {canManage && (
                <Button
                  onClick={() => navigate('/schedules/create')}
                  className="bg-gradient-to-r from-purple-600 to-indigo-600"
                >
                  Criar Primeira Escala
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
