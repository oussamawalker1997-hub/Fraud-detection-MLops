import { useState, useRef } from 'react';

const API_KEY = "mlops-dev-key-2026";
const API_URL = "http://localhost:8080";

export default function App() {
  const [amount, setAmount] = useState(45.5);
  const [time, setTime] = useState(1200);
  const [hiddenVars, setHiddenVars] = useState(Array(28).fill(0));
  
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  const [batchStatus, setBatchStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. STORYTELLING : Scénarios métiers concrets
  const loadScenario = (type: 'coffee' | 'hack') => {
    if (type === 'coffee') {
      setAmount(3.5);
      setTime(36000); // 10:00 AM
      setHiddenVars(Array(28).fill(0.1)); // Variables saines
    } else {
      // VRAIE empreinte mathématique d'une fraude issue du dataset
      setAmount(0.0);
      setTime(406);
      setHiddenVars([
        -2.312226542, 1.951992011, -1.609850732, 3.997905588, -0.522187865,
        -1.426545319, -2.537387306, 1.391657248, -2.770089277, -2.772272145,
        3.202033207, -2.899907388, -0.595221881, -4.289253782, 0.389724120,
        -1.140747180, -2.830055675, -0.016822468, 0.416955705, 0.126910559,
        0.517232371, -0.035049369, -0.465211076, 0.320198199, 0.044519167,
        0.177839798, 0.261145003, -0.143275875
      ]);
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    const payload = {
      Time: time,
      Amount: amount,
      ...Object.fromEntries(hiddenVars.map((v, i) => [`V${i + 1}`, v]))
    };

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setResult(data);
      // 2. LIVE FEED : Ajout au flux en direct
      setHistory(prev => [{ time: new Date().toLocaleTimeString(), amount, data }, ...prev].slice(0, 5));
    } catch (error) {
      console.error(error);
      alert("Erreur de connexion à l'API. Le conteneur Docker tourne-t-il ?");
    }
    setLoading(false);
  };

  // 3. DRAG & DROP : Traitement CSV
  const handleBatchUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setBatchStatus("Envoi en cours...");
    try {
      const res = await fetch(`${API_URL}/predict/batch`, {
        method: 'POST',
        headers: {
          'X-API-Key': API_KEY
        },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setBatchStatus(`✅ Fichier accepté. Analyse en cours (Job ID: ${data.job_id})`);
      } else {
        setBatchStatus(`❌ Erreur: ${data.detail}`);
      }
    } catch (error) {
      setBatchStatus("❌ Erreur de communication avec le serveur.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      <header className="mb-8 flex justify-between items-center max-w-6xl mx-auto">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Fraud Intelligence</h1>
          <p className="text-slate-500">Tableau de Bord Analytique MLOps</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full text-sm font-semibold shadow-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Moteur XGBoost Actif
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        
        <div className="lg:col-span-2 space-y-8">
          
          {/* Panneau Scénarios */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold mb-4">1. Profils d'Achat (Scénarios de test)</h2>
            <div className="flex gap-4">
              <button onClick={() => loadScenario('coffee')} className="flex-1 p-4 border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 rounded-lg text-left transition-colors">
                <div className="font-bold text-emerald-800">☕ Achat Quotidien</div>
                <div className="text-sm text-emerald-600">Café à 3.50$ (Heure de bureau, IP locale)</div>
              </button>
              <button onClick={() => loadScenario('hack')} className="flex-1 p-4 border border-rose-200 bg-rose-50 hover:bg-rose-100 rounded-lg text-left transition-colors">
                <div className="font-bold text-rose-800">🚨 Comportement Suspect</div>
                <div className="text-sm text-rose-600">Achat de 4500$ (3h du matin, IP étrangère)</div>
              </button>
            </div>
          </div>

          {/* Formulaire Temps Réel */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold mb-4">2. Inférence en Temps Réel</h2>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-semibold mb-2">Montant de la transaction ($)</label>
                <input type="number" value={amount} onChange={e => setAmount(Number(e.target.value))} className="w-full p-3 border rounded-lg bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2">Temps écoulé (Secondes)</label>
                <input type="number" value={time} onChange={e => setTime(Number(e.target.value))} className="w-full p-3 border rounded-lg bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>
            </div>
            <button 
              onClick={handlePredict}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg shadow-md transition-colors disabled:opacity-50"
            >
              {loading ? 'Analyse par le modèle en cours...' : '⚡ Évaluer le Risque avec l\'IA'}
            </button>
          </div>

          {/* Panneau Batch (CSV Drag & Drop) */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold mb-4">3. Traitement par Lots (Upload CSV)</h2>
            <div 
              className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <input type="file" ref={fileInputRef} className="hidden" accept=".csv" onChange={handleBatchUpload} />
              <div className="text-slate-600 font-semibold text-lg">📁 Cliquez ici pour importer un fichier CSV</div>
              <div className="text-sm text-slate-400 mt-2">Format attendu : 30 colonnes (Time, V1-V28, Amount)</div>
            </div>
            {batchStatus && (
              <div className="mt-4 p-4 bg-slate-800 text-white rounded-lg text-sm font-medium shadow-inner">
                {batchStatus}
              </div>
            )}
          </div>

        </div>

        {/* Colonne de Droite */}
        <div className="space-y-8">
          
          {/* 4. EXPLICABILITÉ (XAI) */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 min-h-[300px]">
            <h2 className="text-lg font-bold mb-4">Décision de l'IA (XAI)</h2>
            
            {result ? (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="text-center p-6 rounded-xl bg-slate-50 border">
                  <div className="text-sm font-bold text-slate-500 uppercase tracking-wide">Probabilité de Fraude</div>
                  <div className={`text-5xl font-black mt-2 ${result.is_fraud ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {(result.risk_score * 100).toFixed(1)}%
                  </div>
                  <div className={`inline-block mt-4 px-4 py-1 rounded-full text-sm font-bold text-white ${result.is_fraud ? 'bg-rose-500' : 'bg-emerald-500'}`}>
                    {result.risk_level}
                  </div>
                </div>

                <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                  <h3 className="font-bold text-sm mb-3 text-slate-800">🔍 Facteurs Clés d'Analyse :</h3>
                  <ul className="space-y-3">
                    {result.explanations?.map((exp: string, idx: number) => (
                      <li key={idx} className="flex gap-3 items-start text-sm text-slate-600 leading-tight">
                        <span className="text-blue-500 font-bold">→</span> {exp}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-48 text-slate-400 text-sm text-center border-2 border-dashed rounded-xl">
                En attente d'une transaction à évaluer.
              </div>
            )}
          </div>

          {/* 5. LIVE FEED (Historique récent) */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold mb-4">Flux en Direct (Live Feed)</h2>
            <div className="space-y-3">
              {history.length > 0 ? history.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 rounded-lg border bg-slate-50 text-sm animate-in fade-in slide-in-from-left-4">
                  <div>
                    <div className="font-bold">{item.amount}$</div>
                    <div className="text-xs text-slate-500">Heure d'analyse : {item.time}</div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-bold ${item.data.is_fraud ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {item.data.risk_level}
                  </div>
                </div>
              )) : (
                <div className="text-sm text-slate-400 text-center py-8">Aucune activité récente.</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}