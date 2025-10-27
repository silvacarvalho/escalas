import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { User, Edit, Star, Calendar as CalendarIcon, Plus, X } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [unavailableDialogOpen, setUnavailableDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: ''
  });
  const [unavailablePeriod, setUnavailablePeriod] = useState({
    start_date: '',
    end_date: '',
    reason: ''
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      setFormData({
        name: response.data.name,
        email: response.data.email || '',
        phone: response.data.phone || ''
      });
      
      // Update localStorage
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (error) {
      toast.error('Erro ao carregar perfil');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/auth/me`, formData);
      toast.success('Perfil atualizado com sucesso!');
      setEditDialogOpen(false);
      loadProfile();
    } catch (error) {
      toast.error('Erro ao atualizar perfil');
    }
  };

  const handleAddUnavailability = async (e) => {
    e.preventDefault();
    try {
      const updatedPeriods = [
        ...(user.unavailable_periods || []),
        unavailablePeriod
      ];
      
      await axios.put(`${API}/auth/me`, { unavailable_periods: updatedPeriods });
      toast.success('Período de indisponibilidade adicionado!');
      setUnavailableDialogOpen(false);
      setUnavailablePeriod({ start_date: '', end_date: '', reason: '' });
      loadProfile();
    } catch (error) {
      toast.error('Erro ao adicionar período');
    }
  };

  const handleRemoveUnavailability = async (index) => {
    try {
      const updatedPeriods = user.unavailable_periods.filter((_, i) => i !== index);
      await axios.put(`${API}/auth/me`, { unavailable_periods: updatedPeriods });
      toast.success('Período removido com sucesso!');
      loadProfile();
    } catch (error) {
      toast.error('Erro ao remover período');
    }
  };

  const getRoleLabel = (role) => {
    const roles = {
      pastor_distrital: 'Pastor Distrital',
      lider_igreja: 'Líder de Igreja',
      pregador: 'Pregador',
      cantor: 'Cantor',
      membro: 'Membro'
    };
    return roles[role] || role;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateStr) => {
    try {
      return format(new Date(dateStr), "dd 'de' MMMM 'de' yyyy", { locale: ptBR });
    } catch (error) {
      return dateStr;
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

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6" data-testid="profile-container">
        <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Meu Perfil</h1>

        {/* Profile Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <div className="h-20 w-20 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-white text-3xl font-bold">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <CardTitle className="text-2xl mb-1">{user.name}</CardTitle>
                  <Badge className="bg-purple-100 text-purple-800">
                    {getRoleLabel(user.role)}
                  </Badge>
                </div>
              </div>
              <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" data-testid="edit-profile-button">
                    <Edit className="mr-2 h-4 w-4" />
                    Editar
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Editar Perfil</DialogTitle>
                    <DialogDescription>Atualize suas informações pessoais</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleUpdate} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Nome Completo</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Telefone</Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      />
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>
                        Cancelar
                      </Button>
                      <Button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-600">
                        Salvar
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Usuário</p>
                <p className="font-semibold">@{user.username}</p>
              </div>
              {user.email && (
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-semibold">{user.email}</p>
                </div>
              )}
              {user.phone && (
                <div>
                  <p className="text-sm text-gray-500">Telefone</p>
                  <p className="font-semibold">{user.phone}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Scores Card (for preachers/singers) */}
        {(user.is_preacher || user.is_singer) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Star className="h-5 w-5 text-yellow-500" />
                <span>Meus Scores</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {user.is_preacher && (
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-semibold text-gray-700">Pregação</p>
                      <Star className="h-5 w-5 text-green-600" />
                    </div>
                    <p className={`text-4xl font-bold ${getScoreColor(user.preacher_score)}`}>
                      {user.preacher_score.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">de 100</p>
                  </div>
                )}
                {user.is_singer && (
                  <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-200">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-semibold text-gray-700">Louvor Especial</p>
                      <Star className="h-5 w-5 text-orange-600" />
                    </div>
                    <p className={`text-4xl font-bold ${getScoreColor(user.singer_score)}`}>
                      {user.singer_score.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">de 100</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Unavailable Periods Card */}
        {(user.is_preacher || user.is_singer) && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <CalendarIcon className="h-5 w-5 text-purple-600" />
                  <span>Períodos de Indisponibilidade</span>
                </CardTitle>
                <Dialog open={unavailableDialogOpen} onOpenChange={setUnavailableDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" data-testid="add-unavailable-button">
                      <Plus className="mr-2 h-4 w-4" />
                      Adicionar
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Adicionar Período de Indisponibilidade</DialogTitle>
                      <DialogDescription>Informe o período em que você não estará disponível</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleAddUnavailability} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="start_date">Data de Início</Label>
                        <Input
                          id="start_date"
                          type="date"
                          value={unavailablePeriod.start_date}
                          onChange={(e) => setUnavailablePeriod({ ...unavailablePeriod, start_date: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="end_date">Data de Término</Label>
                        <Input
                          id="end_date"
                          type="date"
                          value={unavailablePeriod.end_date}
                          onChange={(e) => setUnavailablePeriod({ ...unavailablePeriod, end_date: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="reason">Motivo</Label>
                        <Textarea
                          id="reason"
                          value={unavailablePeriod.reason}
                          onChange={(e) => setUnavailablePeriod({ ...unavailablePeriod, reason: e.target.value })}
                          placeholder="Ex: Viagem, Férias, etc."
                          required
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <Button type="button" variant="outline" onClick={() => setUnavailableDialogOpen(false)}>
                          Cancelar
                        </Button>
                        <Button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-600">
                          Adicionar
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {user.unavailable_periods && user.unavailable_periods.length > 0 ? (
                <div className="space-y-3">
                  {user.unavailable_periods.map((period, index) => (
                    <div
                      key={index}
                      className="flex items-start justify-between p-4 bg-amber-50 border border-amber-200 rounded-lg"
                      data-testid={`unavailable-period-${index}`}
                    >
                      <div>
                        <p className="font-semibold text-sm">
                          {formatDate(period.start_date)} - {formatDate(period.end_date)}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">{period.reason}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveUnavailability(index)}
                        data-testid={`remove-unavailable-${index}`}
                      >
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-6">Nenhum período de indisponibilidade cadastrado</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
