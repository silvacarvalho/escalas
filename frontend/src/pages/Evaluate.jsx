import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';
import { Star, Send } from 'lucide-react';

export default function Evaluate() {
  const { scheduleItemId } = useParams();
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [rating, setRating] = useState(3);
  const [feedback, setFeedback] = useState('');
  const [scheduleInfo, setScheduleInfo] = useState(null);

  useEffect(() => {
    loadScheduleInfo();
  }, [scheduleItemId]);

  const loadScheduleInfo = async () => {
    try {
      // Try to load schedule info (this will work if user is logged in)
      const response = await axios.get(`${API}/schedules`);
      const allSchedules = response.data;
      
      for (const schedule of allSchedules) {
        const item = schedule.items?.find(i => i.id === scheduleItemId);
        if (item) {
          setScheduleInfo({ schedule, item });
          break;
        }
      }
    } catch (error) {
      console.log('Not logged in - evaluation without context');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // For this to work, we need church_id and evaluated_user_id
      // In a real scenario, these would be passed via URL params or loaded from the schedule
      if (!scheduleInfo) {
        toast.error('Informações do culto não encontradas');
        return;
      }

      await axios.post(`${API}/evaluations`, {
        id_item_escala: scheduleItemId,
        id_igreja: scheduleInfo.schedule.id_igreja,
        tipo_membro: 'pregador',
        id_usuario_avaliado: scheduleInfo.item.id_pregador,
        nota: rating,
        comentario: feedback
      });

      toast.success('Avaliação enviada com sucesso!');
      setSubmitted(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar avaliação');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Card className="max-w-md w-full text-center">
          <CardContent className="py-12">
            <div className="mb-6">
              <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-2">Obrigado pela avaliação!</h2>
              <p className="text-gray-600">Sua opinião é muito importante para nós.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card className="max-w-md w-full" data-testid="evaluation-form">
        <CardHeader>
          <CardTitle className="text-2xl" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Avaliar Pregador
          </CardTitle>
          <p className="text-sm text-gray-500">Sua avaliação é anônima</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <Label className="text-base font-semibold">Como você avalia a pregação?</Label>
              <RadioGroup
                value={rating.toString()}
                onValueChange={(value) => setRating(parseInt(value))}
                className="space-y-2"
              >
                {[5, 4, 3, 2, 1].map((value) => (
                  <div key={value} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-purple-50 transition-all">
                    <RadioGroupItem value={value.toString()} id={`rating-${value}`} />
                    <Label htmlFor={`rating-${value}`} className="flex items-center space-x-2 cursor-pointer flex-1">
                      <div className="flex">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`h-5 w-5 ${
                              i < value ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm">
                        {value === 5 && 'Excelente'}
                        {value === 4 && 'Muito Bom'}
                        {value === 3 && 'Bom'}
                        {value === 2 && 'Regular'}
                        {value === 1 && 'Precisa Melhorar'}
                      </span>
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>

            <div className="space-y-2">
              <Label htmlFor="feedback">Feedback Construtivo (Opcional)</Label>
              <Textarea
                id="feedback"
                data-testid="feedback-textarea"
                placeholder="Compartilhe seus comentários de forma respeitosa..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </div>

            <Button
              type="submit"
              data-testid="submit-evaluation-button"
              className="w-full h-12 text-base font-semibold"
              disabled={loading}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              }}
            >
              {loading ? (
                <span>Enviando...</span>
              ) : (
                <>
                  <Send className="mr-2 h-5 w-5" />
                  Enviar Avaliação
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
