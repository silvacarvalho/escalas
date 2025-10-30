import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';
import { Calendar, Zap, Hand } from 'lucide-react';

export default function ScheduleCreate() {
  const [mode, setMode] = useState('auto');
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [districtId, setDistrictId] = useState('');
  const [churchId, setChurchId] = useState('');
  const [districts, setDistricts] = useState([]);
  const [churches, setChurches] = useState([]);
  const [availableChurches, setAvailableChurches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem('user'));
    setUser(storedUser);
    if (storedUser?.id_distrito) {
      setDistrictId(storedUser.id_distrito);
    }
    loadData();
  }, []);

  useEffect(() => {
    if (districtId && churches.length > 0) {
      loadChurchesForDistrict();
    }
  }, [districtId, month, year, churches]);

  const loadData = async () => {
    try {
      const [districtsRes, churchesRes] = await Promise.all([
        axios.get(`${API}/districts`),
        axios.get(`${API}/churches`)
      ]);
      setDistricts(districtsRes.data);
      setChurches(churchesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    }
  };

  const loadChurchesForDistrict = async () => {
    if (!districtId || churches.length === 0) return;
    
    try {
  const schedulesRes = await axios.get(`${API}/schedules?mes=${month}&ano=${year}&id_distrito=${districtId}`);
  const existingSchedules = schedulesRes.data;
  const existingChurchIds = existingSchedules.map(s => s.id_igreja);
      
      const districtChurches = churches.filter(
        c => c.id_distrito === districtId && !existingChurchIds.includes(c.id)
      );
      
      setAvailableChurches(districtChurches);
    } catch (error) {
      console.error('Error loading churches:', error);
      toast.error('Erro ao carregar igrejas disponíveis');
    }
  };

  const handleAutoGenerate = async () => {
    if (!districtId) {
      toast.error('Selecione um distrito');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/schedules/generate-auto?mes=${month}&ano=${year}&id_distrito=${districtId}`
      );
      
      // A resposta tem o formato { message: string, escalas: string[] }
      if (response.data.escalas?.length > 0) {
        toast.success(response.data.message);
        navigate('/schedules');
      } else {
        toast.error('Não foi possível gerar escalas. Verifique se há pregadores disponíveis.');
      }
    } catch (error) {
      // Pydantic/fastapi validation errors come back as an array under `detail` (objects with keys {type, loc, msg, input, url}).
      // Ensure we convert that into a human-readable string before passing to the toast to avoid React trying to render objects.
      const apiDetail = error?.response?.data?.detail;
      let message = 'Erro ao gerar escalas';
      if (typeof apiDetail === 'string') {
        message = apiDetail;
      } else if (Array.isArray(apiDetail)) {
        message = apiDetail.map(d => d.msg || JSON.stringify(d)).join('; ');
      } else if (apiDetail && typeof apiDetail === 'object') {
        message = apiDetail.msg || JSON.stringify(apiDetail);
      } else if (error?.message) {
        message = error.message;
      }
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualCreate = async () => {
    if (!churchId) {
      toast.error('Selecione uma igreja');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/schedules/manual`, {
        mes: month,
        ano: year,
        id_igreja: churchId,
        modo_geracao: 'manual'
      });

      toast.success('Escala criada com sucesso!');
      navigate(`/schedules/${response.data.id}/calendar`);
    } catch (error) {
      const apiDetail = error?.response?.data?.detail;
      let message = 'Erro ao criar escala';
      if (typeof apiDetail === 'string') {
        message = apiDetail;
      } else if (Array.isArray(apiDetail)) {
        message = apiDetail.map(d => d.msg || JSON.stringify(d)).join('; ');
      } else if (apiDetail && typeof apiDetail === 'object') {
        message = apiDetail.msg || JSON.stringify(apiDetail);
      } else if (error?.message) {
        message = error.message;
      }
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  const years = Array.from({ length: 3 }, (_, i) => new Date().getFullYear() + i);

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6" data-testid="schedule-create-container">
        <div>
          <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Criar Nova Escala
          </h1>
          <p className="text-gray-600">Escolha o modo de geração da escala</p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <RadioGroup value={mode} onValueChange={setMode} className="space-y-4">
              <div
                className={`flex items-start space-x-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  mode === 'auto' ? 'border-purple-600 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
                }`}
                onClick={() => setMode('auto')}
                data-testid="auto-mode-option"
              >
                <RadioGroupItem value="auto" id="auto" className="mt-1" />
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <Zap className="h-5 w-5 text-purple-600" />
                    <Label htmlFor="auto" className="text-lg font-semibold cursor-pointer">
                      Geração Automática
                    </Label>
                  </div>
                  <p className="text-sm text-gray-600">
                    O sistema gera automaticamente a escala para todas as igrejas do distrito,
                    distribuindo pregadores de acordo com seus scores e disponibilidade.
                  </p>
                </div>
              </div>

              <div
                className={`flex items-start space-x-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  mode === 'manual' ? 'border-purple-600 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
                }`}
                onClick={() => setMode('manual')}
                data-testid="manual-mode-option"
              >
                <RadioGroupItem value="manual" id="manual" className="mt-1" />
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <Hand className="h-5 w-5 text-purple-600" />
                    <Label htmlFor="manual" className="text-lg font-semibold cursor-pointer">
                      Geração Manual
                    </Label>
                  </div>
                  <p className="text-sm text-gray-600">
                    Crie uma escala manualmente usando o calendário interativo com drag-and-drop.
                    Permite escalar pregadores de outros distritos.
                  </p>
                </div>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configurações</CardTitle>
            <CardDescription>Defina o período e localização da escala</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="month">Mês</Label>
                <Select
                  value={month.toString()}
                  onValueChange={(value) => setMonth(parseInt(value))}
                >
                  <SelectTrigger data-testid="month-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {months.map((monthName, index) => (
                      <SelectItem key={index} value={(index + 1).toString()}>
                        {monthName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="year">Ano</Label>
                <Select
                  value={year.toString()}
                  onValueChange={(value) => setYear(parseInt(value))}
                >
                  <SelectTrigger data-testid="year-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((y) => (
                      <SelectItem key={y} value={y.toString()}>
                        {y}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {user?.funcao === 'pastor_distrital' && (
              <div className="space-y-2">
                <Label htmlFor="district">Distrito</Label>
                <Select
                  value={districtId}
                  onValueChange={setDistrictId}
                  disabled={mode === 'manual'}
                >
                  <SelectTrigger data-testid="district-select">
                    <SelectValue placeholder="Selecione o distrito" />
                  </SelectTrigger>
                  <SelectContent>
                        {districts.map((district) => (
                      <SelectItem key={district.id} value={district.id}>
                        {district.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {mode === 'manual' && (
              <div className="space-y-2">
                <Label htmlFor="church">Igreja</Label>
                <Select value={churchId} onValueChange={setChurchId}>
                  <SelectTrigger data-testid="church-select">
                    <SelectValue placeholder="Selecione a igreja" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableChurches.map((church) => (
                      <SelectItem key={church.id} value={church.id}>
                        {church.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {availableChurches.length === 0 && districtId && (
                  <p className="text-sm text-amber-600">
                    Todas as igrejas já possuem escalas para este período
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex space-x-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => navigate('/schedules')}
            data-testid="cancel-button"
          >
            Cancelar
          </Button>
          <Button
            className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
            onClick={mode === 'auto' ? handleAutoGenerate : handleManualCreate}
            disabled={loading || (mode === 'manual' && !churchId)}
            data-testid="generate-button"
          >
            {loading ? (
              'Gerando...'
            ) : (
              <>
                <Calendar className="mr-2 h-4 w-4" />
                {mode === 'auto' ? 'Gerar Automaticamente' : 'Criar Escala Manual'}
              </>
            )}
          </Button>
        </div>
      </div>
    </Layout>
  );
}
