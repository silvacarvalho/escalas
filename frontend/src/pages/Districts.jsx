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
import { Plus, Edit, Trash2, MapPin, Church, Users } from 'lucide-react';

export default function Districts() {
  const [districts, setDistricts] = useState([]);
  const [users, setUsers] = useState([]);
  const [churches, setChurches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingDistrict, setEditingDistrict] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    id_pastor: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [districtsRes, usersRes, churchesRes] = await Promise.all([
        axios.get(`${API}/districts`),
        axios.get(`${API}/users`),
        axios.get(`${API}/churches`)
      ]);
      setDistricts(districtsRes.data);
      setUsers(usersRes.data);
      setChurches(churchesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingDistrict) {
        await axios.put(`${API}/districts/${editingDistrict.id}`, formData);
        toast.success('Distrito atualizado com sucesso!');
      } else {
        await axios.post(`${API}/districts`, formData);
        toast.success('Distrito criado com sucesso!');
      }

      setDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar distrito');
    }
  };

  const handleEdit = (district) => {
    setEditingDistrict(district);
    setFormData({
      nome: district.nome,
      id_pastor: district.id_pastor
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este distrito?')) return;
    try {
      await axios.delete(`${API}/districts/${id}`);
      toast.success('Distrito excluído com sucesso!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir distrito');
    }
  };

  const resetForm = () => {
    setEditingDistrict(null);
    setFormData({
      nome: '',
      id_pastor: ''
    });
  };

  const getDistrictStats = (districtId) => {
  const districtChurches = churches.filter(c => c.id_distrito === districtId);
  const districtUsers = users.filter(u => u.id_distrito === districtId);
  const preachers = districtUsers.filter(u => u.eh_pregador);
  const singers = districtUsers.filter(u => u.eh_cantor);
    
    return {
      churches: districtChurches.length,
      users: districtUsers.length,
      preachers: preachers.length,
      singers: singers.length
    };
  };

  const pastors = users.filter(u => u.funcao === 'pastor_distrital');

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
      <div className="space-y-6" data-testid="districts-container">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Distritos</h1>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                data-testid="add-district-button"
              >
                <Plus className="mr-2 h-4 w-4" />
                Novo Distrito
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{editingDistrict ? 'Editar Distrito' : 'Novo Distrito'}</DialogTitle>
                <DialogDescription>Preencha os dados do distrito</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome do Distrito *</Label>
                    <Input
                    id="nome"
                    value={formData.nome}
                    onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                    placeholder="Ex: Distrito Norte"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="id_pastor">Pastor Responsável *</Label>
                  <Select
                    value={formData.id_pastor}
                    onValueChange={(value) => setFormData({ ...formData, id_pastor: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o pastor" />
                    </SelectTrigger>
                    <SelectContent>
                      {pastors.map((pastor) => (
                        <SelectItem key={pastor.id} value={pastor.id}>
                          {pastor.nome_completo}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-600">
                    {editingDistrict ? 'Atualizar' : 'Criar'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {districts.map((district) => {
            const pastor = users.find(u => u.id === district.id_pastor);
            const stats = getDistrictStats(district.id);
            
            return (
              <Card key={district.id} className="hover:shadow-lg transition-all" data-testid={`district-card-${district.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center space-x-2 mb-2">
                        <MapPin className="h-5 w-5 text-purple-600" />
                        <span>{district.nome}</span>
                      </CardTitle>
                      {pastor && (
                        <p className="text-sm text-gray-600">
                          <span className="font-semibold">Pastor:</span> {pastor.nome_completo}
                        </p>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Statistics */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-purple-50 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <Church className="h-5 w-5 text-purple-600" />
                          <span className="text-2xl font-bold text-purple-600">{stats.churches}</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">Igrejas</p>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <Users className="h-5 w-5 text-blue-600" />
                          <span className="text-2xl font-bold text-blue-600">{stats.users}</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">Membros</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Pregadores:</span>
                      <span className="font-semibold text-green-600">{stats.preachers}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Cantores:</span>
                      <span className="font-semibold text-orange-600">{stats.singers}</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 mt-4 pt-4 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(district)}
                      data-testid={`edit-district-${district.id}`}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(district.id)}
                      data-testid={`delete-district-${district.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {districts.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Nenhum distrito cadastrado</p>
              <Button
                onClick={() => setDialogOpen(true)}
                className="bg-gradient-to-r from-purple-600 to-indigo-600"
              >
                Criar Primeiro Distrito
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
