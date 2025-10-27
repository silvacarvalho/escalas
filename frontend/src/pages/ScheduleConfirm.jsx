import React from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent } from '@/components/ui/card';

export default function ScheduleConfirm() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Confirmar Escala</h1>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">Página de confirmação de participação</p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
