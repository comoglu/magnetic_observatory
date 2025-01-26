import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const SolarWindPanel = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await window.fs.readFile('solar-wind-data.json', { encoding: 'utf8' });
        const parsedData = JSON.parse(response);
        setData(parsedData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Card className="w-full h-96">
        <CardHeader>
          <CardTitle>Solar Wind Parameters</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-full">
          <p>Loading solar wind data...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full h-96">
        <CardHeader>
          <CardTitle>Solar Wind Parameters</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-red-500">Error loading data: {error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full h-96">
      <CardHeader>
        <CardTitle>Solar Wind Parameters</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="datetime" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="speed" 
              stroke="#8884d8" 
              name="Speed (km/s)"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="density" 
              stroke="#82ca9d" 
              name="Density (p/cm³)"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="temperature" 
              stroke="#ffc658" 
              name="Temperature (K)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default SolarWindPanel;