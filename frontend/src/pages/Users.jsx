import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Users as UsersIcon, Star } from 'lucide-react';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [churches, setChurches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    email: '',
    phone: '',
    role: 'pregador',
    district_id: '',
    church_id: '',
    is_preacher: false,
    is_singer: false
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [usersRes, districtsRes, churchesRes] = await Promise.all([
        axios.get(`${API}/users`),
        axios.get(`${API}/districts`),
        axios.get(`${API}/churches`)
      ]);
      setUsers(usersRes.data);
      setDistricts(districtsRes.data);
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
      if (editingUser) {
        const updateData = { ...formData };
        delete updateData.password; // Don't send password on update
        delete updateData.username; // Don't send username on update
        
        await axios.put(`${API}/users/${editingUser.id}`, updateData);
        toast.success('Usuário atualizado com sucesso!');
      } else {
        await axios.post(`${API}/users`, formData);
        toast.success('Usuário criado com sucesso!');
      }

      setDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar usuário');
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      name: user.name,
      email: user.email || '',
      phone: user.phone || '',
      role: user.role,
      district_id: user.district_id || '',
      church_id: user.church_id || '',
      is_preacher: user.is_preacher,
      is_singer: user.is_singer
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este usuário?')) return;
    try {
      await axios.delete(`${API}/users/${id}`);
      toast.success('Usuário excluído com sucesso!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir usuário');
    }
  };

  const resetForm = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      name: '',
      email: '',
      phone: '',
      role: 'pregador',
      district_id: '',
      church_id: '',
      is_preacher: false,
      is_singer: false
    });
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

  const getRoleBadgeColor = (role) => {
    const colors = {
      pastor_distrital: 'bg-purple-100 text-purple-800',
      lider_igreja: 'bg-blue-100 text-blue-800',
      pregador: 'bg-green-100 text-green-800',
      cantor: 'bg-orange-100 text-orange-800',
      membro: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
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

  return (
    <Layout>
      <div className="space-y-6" data-testid="users-container">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Usuários</h1>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                data-testid="add-user-button"
              >
                <Plus className="mr-2 h-4 w-4" />
                Novo Usuário
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingUser ? 'Editar Usuário' : 'Novo Usuário'}</DialogTitle>
                <DialogDescription>Preencha os dados do usuário</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nome Completo *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="username">Usuário *</Label>
                    <Input
                      id="username"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      required
                      disabled={editingUser}
                    />
                  </div>
                </div>

                {!editingUser && (
                  <div className="space-y-2">
                    <Label htmlFor="password">Senha *</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required={!editingUser}
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
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
                      placeholder="+55 11 99999-9999"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Função *</Label>
                  <Select
                    value={formData.role}
                    onValueChange={(value) => setFormData({ ...formData, role: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pastor_distrital">Pastor Distrital</SelectItem>
                      <SelectItem value="lider_igreja">Líder de Igreja</SelectItem>
                      <SelectItem value="pregador">Pregador</SelectItem>
                      <SelectItem value="cantor">Cantor</SelectItem>
                      <SelectItem value="membro">Membro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="district_id">Distrito</Label>
                    <Select
                      value={formData.district_id}
                      onValueChange={(value) => setFormData({ ...formData, district_id: value })}
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
                    <Label htmlFor="church_id">Igreja</Label>
                    <Select
                      value={formData.church_id}
                      onValueChange={(value) => setFormData({ ...formData, church_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione a igreja" />
                      </SelectTrigger>
                      <SelectContent>
                        {churches
                          .filter(c => !formData.district_id || c.district_id === formData.district_id)
                          .map((church) => (
                            <SelectItem key={church.id} value={church.id}>
                              {church.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Habilidades</Label>
                  <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="is_preacher"
                        checked={formData.is_preacher}
                        onCheckedChange={(checked) => setFormData({ ...formData, is_preacher: checked })}
                      />
                      <Label htmlFor="is_preacher" className="cursor-pointer">É Pregador</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="is_singer"
                        checked={formData.is_singer}
                        onCheckedChange={(checked) => setFormData({ ...formData, is_singer: checked })}
                      />
                      <Label htmlFor="is_singer" className="cursor-pointer">É Cantor</Label>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-600">
                    {editingUser ? 'Atualizar' : 'Criar'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {users.map((user) => {
            const district = districts.find(d => d.id === user.district_id);
            const church = churches.find(c => c.id === user.church_id);
            
            return (
              <Card key={user.id} className="hover:shadow-lg transition-all" data-testid={`user-card-${user.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center space-x-2 mb-2">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold">
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-base">{user.name}</p>
                          <p className="text-xs text-gray-500 font-normal">@{user.username}</p>
                        </div>
                      </CardTitle>
                    </div>
                    <Badge className={getRoleBadgeColor(user.role)}>
                      {getRoleLabel(user.role)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {user.email && (
                      <p className="text-gray-600 truncate">
                        <span className="font-semibold">Email:</span> {user.email}
                      </p>
                    )}
                    {user.phone && (
                      <p className="text-gray-600">
                        <span className="font-semibold">Telefone:</span> {user.phone}
                      </p>
                    )}
                    {district && (
                      <p className="text-gray-600">
                        <span className="font-semibold">Distrito:</span> {district.name}
                      </p>
                    )}
                    {church && (
                      <p className="text-gray-600">
                        <span className="font-semibold">Igreja:</span> {church.name}
                      </p>
                    )}
                    
                    <div className="flex gap-2 pt-2">
                      {user.is_preacher && (
                        <Badge variant="outline" className="text-xs">
                          Pregador
                          <Star className={`ml-1 h-3 w-3 ${getScoreColor(user.preacher_score)}`} />
                          <span className={`ml-1 ${getScoreColor(user.preacher_score)}`}>
                            {user.preacher_score.toFixed(0)}
                          </span>
                        </Badge>
                      )}
                      {user.is_singer && (
                        <Badge variant="outline" className="text-xs">
                          Cantor
                          <Star className={`ml-1 h-3 w-3 ${getScoreColor(user.singer_score)}`} />
                          <span className={`ml-1 ${getScoreColor(user.singer_score)}`}>
                            {user.singer_score.toFixed(0)}
                          </span>
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(user)}
                      data-testid={`edit-user-${user.id}`}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(user.id)}
                      data-testid={`delete-user-${user.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {users.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <UsersIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Nenhum usuário cadastrado</p>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
