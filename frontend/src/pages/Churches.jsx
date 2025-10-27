import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Church as ChurchIcon } from 'lucide-react';

export default function Churches() {
  const [churches, setChurches] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingChurch, setEditingChurch] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    district_id: '',
    address: '',
    latitude: '',
    longitude: '',
    leader_id: '',
    service_schedule: []
  });
  const [serviceDays, setServiceDays] = useState([{ day_of_week: 'saturday', time: '09:00' }]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [churchesRes, districtsRes, usersRes] = await Promise.all([
        axios.get(`${API}/churches`),
        axios.get(`${API}/districts`),
        axios.get(`${API}/users?is_preacher=true`)
      ]);
      setChurches(churchesRes.data);
      setDistricts(districtsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        latitude: formData.latitude ? parseFloat(formData.latitude) : null,
        longitude: formData.longitude ? parseFloat(formData.longitude) : null,
        service_schedule: serviceDays
      };

      if (editingChurch) {
        await axios.put(`${API}/churches/${editingChurch.id}`, payload);
        toast.success('Igreja atualizada com sucesso!');
      } else {
        await axios.post(`${API}/churches`, payload);
        toast.success('Igreja criada com sucesso!');
      }

      setDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar igreja');
    }
  };

  const handleEdit = (church) => {
    setEditingChurch(church);
    setFormData({
      name: church.name,
      district_id: church.district_id,
      address: church.address || '',
      latitude: church.latitude || '',
      longitude: church.longitude || '',
      leader_id: church.leader_id || ''
    });
    setServiceDays(church.service_schedule?.length > 0 ? church.service_schedule : [{ day_of_week: 'saturday', time: '09:00' }]);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta igreja?')) return;
    try {
      await axios.delete(`${API}/churches/${id}`);
      toast.success('Igreja excluída com sucesso!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir igreja');
    }
  };

  const resetForm = () => {
    setEditingChurch(null);
    setFormData({
      name: '',
      district_id: '',
      address: '',
      latitude: '',
      longitude: '',
      leader_id: '',
      service_schedule: []
    });
    setServiceDays([{ day_of_week: 'saturday', time: '09:00' }]);
  };

  const addServiceDay = () => {
    setServiceDays([...serviceDays, { day_of_week: 'wednesday', time: '19:00' }]);
  };

  const removeServiceDay = (index) => {
    setServiceDays(serviceDays.filter((_, i) => i !== index));
  };

  const updateServiceDay = (index, field, value) => {
    const updated = [...serviceDays];
    updated[index][field] = value;
    setServiceDays(updated);
  };

  const dayOptions = [
    { value: 'monday', label: 'Segunda-feira' },
    { value: 'tuesday', label: 'Terça-feira' },
    { value: 'wednesday', label: 'Quarta-feira' },
    { value: 'thursday', label: 'Quinta-feira' },
    { value: 'friday', label: 'Sexta-feira' },
    { value: 'saturday', label: 'Sábado' },
    { value: 'sunday', label: 'Domingo' }
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
      <div className="space-y-6" data-testid="churches-container">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Igrejas</h1>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                data-testid="add-church-button"
              >
                <Plus className="mr-2 h-4 w-4" />
                Nova Igreja
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingChurch ? 'Editar Igreja' : 'Nova Igreja'}</DialogTitle>
                <DialogDescription>Preencha os dados da igreja</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="district_id">Distrito *</Label>
                  <Select
                    value={formData.district_id}
                    onValueChange={(value) => setFormData({ ...formData, district_id: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o distrito" />
                    </SelectTrigger>
                    <SelectContent>
                      {districts.map((district) => (
                        <SelectItem key={district.id} value={district.id}>
                          {district.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Endereço</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="latitude">Latitude</Label>
                    <Input
                      id="latitude"
                      type="number"
                      step="any"
                      value={formData.latitude}
                      onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="longitude">Longitude</Label>
                    <Input
                      id="longitude"
                      type="number"
                      step="any"
                      value={formData.longitude}
                      onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="leader_id">Líder da Igreja</Label>
                  <Select
                    value={formData.leader_id}
                    onValueChange={(value) => setFormData({ ...formData, leader_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o líder" />
                    </SelectTrigger>
                    <SelectContent>
                      {users.map((user) => (
                        <SelectItem key={user.id} value={user.id}>
                          {user.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Horários de Culto *</Label>
                    <Button type="button" size="sm" onClick={addServiceDay} variant="outline">
                      <Plus className="h-4 w-4 mr-1" /> Adicionar
                    </Button>
                  </div>
                  {serviceDays.map((day, index) => (
                    <div key={index} className="flex gap-2">
                      <Select
                        value={day.day_of_week}
                        onValueChange={(value) => updateServiceDay(index, 'day_of_week', value)}
                      >
                        <SelectTrigger className="flex-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {dayOptions.map((opt) => (
                            <SelectItem key={opt.value} value={opt.value}>
                              {opt.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Input
                        type="time"
                        value={day.time}
                        onChange={(e) => updateServiceDay(index, 'time', e.target.value)}
                        className="w-32"
                      />
                      {serviceDays.length > 1 && (
                        <Button
                          type="button"
                          size="icon"
                          variant="outline"
                          onClick={() => removeServiceDay(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-600">
                    {editingChurch ? 'Atualizar' : 'Criar'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {churches.map((church) => {
            const district = districts.find(d => d.id === church.district_id);
            const leader = users.find(u => u.id === church.leader_id);
            
            return (
              <Card key={church.id} className="hover:shadow-lg transition-all" data-testid={`church-card-${church.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center space-x-2 mb-2">
                        <ChurchIcon className="h-5 w-5 text-purple-600" />
                        <span>{church.name}</span>
                      </CardTitle>
                      <p className="text-sm text-gray-500">{district?.name || 'Distrito não encontrado'}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {church.address && (
                      <p className="text-gray-600">
                        <span className="font-semibold">Endereço:</span> {church.address}
                      </p>
                    )}
                    {leader && (
                      <p className="text-gray-600">
                        <span className="font-semibold">Líder:</span> {leader.name}
                      </p>
                    )}
                    {church.service_schedule?.length > 0 && (
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">Cultos:</p>
                        {church.service_schedule.map((schedule, idx) => (
                          <p key={idx} className="text-gray-600 ml-2">
                            {dayOptions.find(d => d.value === schedule.day_of_week)?.label} - {schedule.time}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex space-x-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(church)}
                      data-testid={`edit-church-${church.id}`}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(church.id)}
                      data-testid={`delete-church-${church.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {churches.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <ChurchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Nenhuma igreja cadastrada</p>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
