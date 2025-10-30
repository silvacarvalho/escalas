import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        nome_usuario: username,
        senha: password,
      });

      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      toast.success('Login realizado com sucesso!');
      navigate('/');
    } catch (error) {
      // Garantir que passamos uma string para o toast (React não aceita objetos como children)
      console.error('Login error:', error);
      const detail = error.response?.data?.detail;
      let message = 'Credenciais inválidas';
      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        // pydantic/fastapi pode retornar uma lista de erros
        message = detail
          .map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d)))
          .join('; ');
      } else if (detail && typeof detail === 'object') {
        message = detail.msg || JSON.stringify(detail);
      } else if (error.message) {
        message = error.message;
      }
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card className="w-full max-w-md shadow-2xl" data-testid="login-card">
        <CardHeader className="space-y-3 text-center">
          <CardTitle className="text-3xl font-bold" style={{
            fontFamily: 'Space Grotesk, sans-serif',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>APOSTELLO</CardTitle>
          <CardDescription className="text-base">Controle de Escalas: Pregação e Louvor Especial</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Usuário</Label>
              <Input
                id="username"
                data-testid="username-input"
                type="text"
                placeholder="Digite seu usuário"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="h-11"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                data-testid="password-input"
                type="password"
                placeholder="Digite sua senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-11"
              />
            </div>
            <Button
              type="submit"
              data-testid="login-button"
              className="w-full h-11 text-base font-semibold"
              disabled={loading}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none'
              }}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
