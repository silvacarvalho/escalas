import React from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent } from '@/components/ui/card';

export default function Districts() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Distritos</h1>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">Página de gerenciamento de distritos</p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
