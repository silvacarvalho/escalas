import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, Users, Star, Church as ChurchIcon, Calendar, Award } from 'lucide-react';

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem('user'));
    setUser(storedUser);
    
    if (storedUser?.role === 'pastor_distrital' && storedUser?.district_id) {
      loadAnalytics(storedUser.district_id);
    } else {
      setLoading(false);
    }
  }, []);

  const loadAnalytics = async (districtId) => {
    try {
      const response = await axios.get(`${API}/analytics/dashboard?district_id=${districtId}`);
      setAnalytics(response.data);
    } catch (error) {
      toast.error('Erro ao carregar analytics');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeColor = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
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

  if (!analytics || user?.role !== 'pastor_distrital') {
    return (
      <Layout>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Analytics</h1>
          <Card>
            <CardContent className="py-12 text-center">
              <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Analytics disponível apenas para Pastores Distritais</p>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="analytics-container">
        <div>
          <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Analytics</h1>
          <p className="text-gray-600">Métricas e estatísticas do distrito</p>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total de Igrejas</p>
                  <p className="text-4xl font-bold text-purple-600">{analytics.total_churches}</p>
                </div>
                <ChurchIcon className="h-12 w-12 text-purple-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Pregadores Ativos</p>
                  <p className="text-4xl font-bold text-green-600">{analytics.total_preachers}</p>
                </div>
                <Users className="h-12 w-12 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Cantores Ativos</p>
                  <p className="text-4xl font-bold text-orange-600">{analytics.total_singers}</p>
                </div>
                <Users className="h-12 w-12 text-orange-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Performers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Preachers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Award className="h-5 w-5 text-yellow-500" />
                <span>Top Pregadores</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.top_preachers && analytics.top_preachers.length > 0 ? (
                  analytics.top_preachers.slice(0, 10).map((preacher, index) => (
                    <div
                      key={preacher.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`flex items-center justify-center h-8 w-8 rounded-full ${
                          index === 0 ? 'bg-yellow-400' :
                          index === 1 ? 'bg-gray-300' :
                          index === 2 ? 'bg-orange-400' :
                          'bg-gray-200'
                        } text-white font-bold text-sm`}>
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-semibold text-sm">{preacher.name}</p>
                          <p className="text-xs text-gray-500">@{preacher.username}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Star className={`h-4 w-4 ${getScoreColor(preacher.preacher_score)}`} />
                        <Badge className={getScoreBadgeColor(preacher.preacher_score)}>
                          {preacher.preacher_score.toFixed(1)}
                        </Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-gray-500 py-6">Nenhum pregador encontrado</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recent Evaluations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Star className="h-5 w-5 text-purple-600" />
                <span>Avaliações Recentes</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.recent_evaluations && analytics.recent_evaluations.length > 0 ? (
                  analytics.recent_evaluations.map((evaluation) => {
                    const ratingStars = Array(5).fill(0).map((_, i) => (
                      <Star
                        key={i}
                        className={`h-3 w-3 inline ${
                          i < evaluation.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                        }`}
                      />
                    ));

                    return (
                      <div
                        key={evaluation.id}
                        className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-sm font-semibold text-gray-700">
                            {evaluation.member_type === 'preacher' ? 'Pregação' : 'Louvor Especial'}
                          </p>
                          <div className="flex items-center space-x-1">
                            {ratingStars}
                          </div>
                        </div>
                        {evaluation.feedback && (
                          <p className="text-xs text-gray-600 italic">"{evaluation.feedback}"</p>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-center text-gray-500 py-6">Nenhuma avaliação recente</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <span>Insights de Desempenho</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <p className="text-xs font-semibold text-gray-700">Média Geral</p>
                </div>
                <p className="text-2xl font-bold text-blue-600">
                  {analytics.top_preachers && analytics.top_preachers.length > 0
                    ? (analytics.top_preachers.reduce((acc, p) => acc + p.preacher_score, 0) / analytics.top_preachers.length).toFixed(1)
                    : '0.0'
                  }
                </p>
                <p className="text-xs text-gray-500 mt-1">Score médio dos pregadores</p>
              </div>

              <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
                <div className="flex items-center space-x-2 mb-2">
                  <Award className="h-4 w-4 text-green-600" />
                  <p className="text-xs font-semibold text-gray-700">Alto Desempenho</p>
                </div>
                <p className="text-2xl font-bold text-green-600">
                  {analytics.top_preachers ? analytics.top_preachers.filter(p => p.preacher_score >= 80).length : 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">Pregadores com score ≥ 80</p>
              </div>

              <div className="p-4 bg-gradient-to-br from-yellow-50 to-amber-50 rounded-lg border border-yellow-200">
                <div className="flex items-center space-x-2 mb-2">
                  <Star className="h-4 w-4 text-yellow-600" />
                  <p className="text-xs font-semibold text-gray-700">Médio Desempenho</p>
                </div>
                <p className="text-2xl font-bold text-yellow-600">
                  {analytics.top_preachers ? analytics.top_preachers.filter(p => p.preacher_score >= 60 && p.preacher_score < 80).length : 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">Pregadores com score 60-79</p>
              </div>

              <div className="p-4 bg-gradient-to-br from-red-50 to-rose-50 rounded-lg border border-red-200">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingDown className="h-4 w-4 text-red-600" />
                  <p className="text-xs font-semibold text-gray-700">Necessita Atenção</p>
                </div>
                <p className="text-2xl font-bold text-red-600">
                  {analytics.top_preachers ? analytics.top_preachers.filter(p => p.preacher_score < 60).length : 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">Pregadores com score < 60</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
