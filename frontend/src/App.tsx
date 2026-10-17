import { useEffect, useState } from "react";
import { Card, Text, Metric, Grid, BadgeDelta, Badge, Button, NumberInput, Divider, Callout, ProgressBar } from "@tremor/react";
import { Activity, AlertTriangle, CheckCircle, XCircle, ShieldCheck, ShieldAlert, Zap, Cpu } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function App() {
  const [apiStatus, setApiStatus] = useState<"checking" | "healthy" | "error">("checking");
  const [modelVersion, setModelVersion] = useState<string>("Loading...");

  // Structure exacte de la classe Pydantic
  const [formData, setFormData] = useState({
    Time: 0, Amount: 150.00,
    V1: 0, V2: 0, V3: 0, V4: 0, V5: 0, V6: 0, V7: 0, V8: 0, V9: 0, V10: 0,
    V11: 0, V12: 0, V13: 0, V14: 0, V15: 0, V16: 0, V17: 0, V18: 0, V19: 0, V20: 0,
    V21: 0, V22: 0, V23: 0, V24: 0, V25: 0, V26: 0, V27: 0, V28: 0
  });

  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [isFraud, setIsFraud] = useState<boolean | null>(null);
  const [riskLevel, setRiskLevel] = useState<string>("");

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

  // Générateurs de profils pour tester l'IA
  const loadSafeTransaction = () => {
    setFormData({
      ...formData, Amount: 45.50, Time: 1200, 
      V1: 1.2, V2: 0.1, V3: 0.5, V4: 0.2, V14: 0.1, V17: -0.2 // Profil normal
    });
  };

  const loadFraudTransaction = () => {
    setFormData({
      ...formData, Amount: 999.99, Time: 406, 
      V1: -2.3, V2: 1.5, V3: -4.5, V4: 3.2, V14: -5.6, V17: -6.2 // Profil fraude typique
    });
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPredicting(true);
    setRiskScore(null);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("Erreur de l'API");
      const data = await response.json();
      
      setIsFraud(data.is_fraud === 1); 
    setRiskScore(Number((data.risk_score * 100).toFixed(2)));
      setRiskLevel(data.risk_level);

    } catch (error) {
      console.error("Erreur:", error);
      alert("Échec de la prédiction.");
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Fraud Intelligence</h1>
            <p className="text-slate-500 mt-1">Real-Time Risk Analytics Platform</p>
          </div>
          {apiStatus === "healthy" ? <Badge color="emerald" icon={CheckCircle}>API Connected</Badge> : <Badge color="red" icon={XCircle}>Offline</Badge>}
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
            <Text>Active AI Engine</Text>
            <Metric className="truncate" title={modelVersion}>{modelVersion.split('/').pop() || 'Loading...'}</Metric>
            <Text className="mt-2 text-xs">Cloud Run Inference Active</Text>
          </Card>
        </Grid>

        <Grid numItemsSm={1} numItemsLg={3} className="gap-6 mt-8">
          {/* Colonne Formulaire */}
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <Text className="font-semibold text-lg text-slate-700">Live Transaction Scoring</Text>
              <div className="flex gap-2">
                <Button size="xs" color="emerald" variant="secondary" onClick={loadSafeTransaction}>Load Safe Profile</Button>
                <Button size="xs" color="red" variant="secondary" onClick={loadFraudTransaction}>Load Fraud Profile</Button>
              </div>
            </div>
            <Divider />
            
            <form onSubmit={handlePredict} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Text className="mb-1 font-medium">Amount ($)</Text>
                  <NumberInput 
                    value={formData.Amount} 
                    onChange={(e) => setFormData({...formData, Amount: Number(e.target.value)})} 
                  />
                </div>
                <div>
                  <Text className="mb-1 font-medium">Time (Seconds)</Text>
                  <NumberInput 
                    value={formData.Time} 
                    onChange={(e) => setFormData({...formData, Time: Number(e.target.value)})} 
                  />
                </div>
              </div>
              
              <div className="bg-slate-100 p-3 rounded-lg flex items-center gap-2 text-sm text-slate-500">
                <Cpu className="w-4 h-4" />
                <span>28 hidden PCA variables (V1-V28) are auto-populated based on the selected profile for model compatibility.</span>
              </div>

              <div className="pt-4">
                <Button 
                  type="submit" size="lg" icon={Zap} loading={isPredicting} 
                  loadingText="Running XGBoost Inference..." className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  Analyze Transaction Risk
                </Button>
              </div>
            </form>
          </Card>

          {/* Colonne Résultats */}
          <Card>
            <Text className="font-semibold text-lg text-slate-700 mb-4">Risk Assessment</Text>
            <Divider />
            
            {riskScore === null ? (
              <div className="h-48 flex items-center justify-center text-slate-400 text-sm text-center">
                Submit a transaction to view<br/>the AI fraud probability score.
              </div>
            ) : (
              <div className="space-y-6">
                <div className="text-center">
                 <Text>Fraud Risk Probability</Text>
                  <Metric className={isFraud ? "text-red-600" : "text-emerald-600"}>
                    {riskScore}%
                  </Metric>
                  <Badge size="xs" color={isFraud ? "red" : "emerald"} className="mt-2">
                    {riskLevel}
                  </Badge>
                </div>
                
                <ProgressBar value={riskScore} color={isFraud ? "red" : "emerald"} className="mt-2" />

                {isFraud ? (
                  <Callout title="High Fraud Risk Detected" icon={ShieldAlert} color="red">
                    The AI flagged this transaction as highly anomalous. Immediate manual review recommended.
                  </Callout>
                ) : (
                  <Callout title="Transaction Safe" icon={ShieldCheck} color="emerald">
                    Behavior aligns with standard customer patterns. No anomalies detected.
                  </Callout>
                )}
              </div>
            )}
          </Card>
        </Grid>
      </div>
    </div>
  );
}