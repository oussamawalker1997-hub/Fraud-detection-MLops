import { useEffect, useState } from "react";
import { Card, Text, Metric, Grid, BadgeDelta, Badge } from "@tremor/react";
import { Activity, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function App() {
  const [apiStatus, setApiStatus] = useState<"checking" | "healthy" | "error">("checking");
  const [modelVersion, setModelVersion] = useState<string>("Loading...");

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => {
        if (!res.ok) throw new Error("API not responding");
        return res.json();
      })
      .then((data) => {
        setApiStatus("healthy");
        setModelVersion(data.model_uri === "not_set" ? "Model Missing" : "Model Loaded");
      })
      .catch(() => {
        setApiStatus("error");
        setModelVersion("Offline");
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Fraud Intelligence</h1>
            <p className="text-slate-500 mt-1">Real-Time Risk Analytics Platform</p>
          </div>
          
          {apiStatus === "checking" && <Badge color="yellow">Checking API...</Badge>}
          {apiStatus === "healthy" && (
            <Badge color="emerald" icon={CheckCircle}>API Connected</Badge>
          )}
          {apiStatus === "error" && (
            <Badge color="red" icon={XCircle}>API Offline / CORS Error</Badge>
          )}
        </div>

        <Grid numItemsSm={2} numItemsLg={3} className="gap-6">
          <Card decoration="top" decorationColor="blue">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              <Text>Transactions Analyzed</Text>
            </div>
            <Metric>1,245</Metric>
          </Card>
          
          <Card decoration="top" decorationColor="red">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <Text>Fraud Detections</Text>
            </div>
            <div className="flex items-center justify-between">
              <Metric>12</Metric>
              <BadgeDelta deltaType="moderateIncrease">1.2% rate</BadgeDelta>
            </div>
          </Card>

          <Card decoration="top" decorationColor="emerald">
            <Text>API Model Status</Text>
            <Metric>{modelVersion}</Metric>
            <Text className="mt-2 text-xs">Fetched directly from Cloud Run</Text>
          </Card>
        </Grid>

      </div>
    </div>
  );
}