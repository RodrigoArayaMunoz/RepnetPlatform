import "../styles/LoadVehicleDictionary.css";
import { useEffect, useState } from "react";
import ResultModal from "../components/ResultModal";

function ProcessingOverlay({ visible, progress = 0, message = "" }) {
  if (!visible) return null;

  return (
    <div className="processing-overlay">
      <div className="processing-box">
        <div className="processing-spinner" />
        <h2>Generando diccionario vehicular</h2>
        <p className="processing-progress">{progress}%</p>
        <p className="processing-message">
          {message || "Procesando..."}
        </p>

        <div className="processing-bar">
          <div
            className="processing-bar-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function LoadVehicleDictionary() {
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  const [mlConnected, setMlConnected] = useState(false);
  const [mlVerified, setMlVerified] = useState(false);
  const [mlUserId, setMlUserId] = useState(null);
  const [checkingConnection, setCheckingConnection] = useState(true);
  const [mlStatusMessage, setMlStatusMessage] = useState(
    "Verificando conexión con Mercado Libre..."
  );

  const [jobResult, setJobResult] = useState(null);
  const [loadingResult, setLoadingResult] = useState(false);

  const [jobId, setJobId] = useState(null);

  const [loadingProcess, setLoadingProcess] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processMessage, setProcessMessage] = useState("");
  const [showResultModal, setShowResultModal] = useState(false);

  const API_BASE =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    checkMlConnection();
  }, []);

  const handleCloseResultModal = () => {
    setShowResultModal(false);
    setJobId(null);
    setJobResult(null);
    setProgress(0);
    setProcessMessage("");
    setStatus("idle");
    setMessage("");
  };

  const checkMlConnection = async () => {
    try {
      setCheckingConnection(true);
      setMlVerified(false);
      setMlConnected(false);
      setMlUserId(null);
      setMlStatusMessage("Verificando conexión con Mercado Libre...");

      const res = await fetch(`${API_BASE}/ml/status`, {
        method: "GET",
        credentials: "include",
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok && data?.connected === true) {
        setMlConnected(true);
        setMlVerified(true);
        setMlUserId(data?.user_id ? String(data.user_id) : null);
        setMlStatusMessage("Conectado exitosamente");
      } else {
        setMlConnected(false);
        setMlVerified(false);
        setMlUserId(null);
        setMlStatusMessage("Debes conectar tu cuenta de Mercado Libre");
      }
    } catch (error) {
      setMlConnected(false);
      setMlVerified(false);
      setMlUserId(null);
      setMlStatusMessage("No se pudo verificar la conexión con Mercado Libre");
    } finally {
      setCheckingConnection(false);
    }
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const pollJob = async (currentJobId) => {
    let finished = false;

    while (!finished) {
      const r = await fetch(`${API_BASE}/imports/${currentJobId}`, {
        credentials: "include",
      });

      const data = await r.json().catch(() => ({}));

      if (!r.ok) {
        throw new Error(
          data?.detail || data?.message || "Error consultando el estado del proceso."
        );
      }

      const currentProgress =
        typeof data.progress === "number" ? data.progress : 0;

      setProgress(Math.min(100, currentProgress));
      setProcessMessage(data.message || "Procesando...");
      setMessage(data.message || "");

      if (data.status === "success") {
        finished = true;
        return data;
      }

      if (data.status === "error") {
        throw new Error(data.message || "Error al generar el diccionario vehicular.");
      }

      await sleep(1200);
    }
  };

  const fetchJobResult = async (currentJobId) => {
    const res = await fetch(`${API_BASE}/imports/${currentJobId}/result`, {
      method: "GET",
      credentials: "include",
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(
        data?.detail || data?.message || "No se pudo obtener el resultado final."
      );
    }

    setJobResult(data);
    setShowResultModal(true);
  };

  const handleGenerateDictionary = async () => {
    if (!mlVerified) {
      setStatus("error");
      setMessage("Primero debes conectar tu cuenta de Mercado Libre.");
      return;
    }

    if (!mlUserId) {
      setStatus("error");
      setMessage("No se encontró user_id asociado a la conexión de Mercado Libre.");
      return;
    }

    try {
      setShowResultModal(false);
      setJobResult(null);
      setStatus("processing");
      setLoadingProcess(true);
      setLoadingResult(false);
      setProgress(0);
      setMessage("");
      setProcessMessage("Iniciando generación del diccionario vehicular...");

      // Reemplaza este endpoint por el real de tu backend
      const res = await fetch(`${API_BASE}/vehicle-dictionary/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: String(mlUserId),
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "No se pudo iniciar la generación del diccionario vehicular."
        );
      }

      if (!data?.job_id) {
        throw new Error("No se recibió job_id del proceso.");
      }

      setJobId(data.job_id);

      await pollJob(data.job_id);

      setProgress(100);
      setStatus("success");

      try {
        setLoadingResult(true);
        await fetchJobResult(data.job_id);
      } catch (error) {
        setStatus("error");
        setMessage(
          error?.message ||
            "El proceso terminó, pero no se pudo obtener el resumen."
        );
      } finally {
        setLoadingResult(false);
        setLoadingProcess(false);
      }
    } catch (error) {
      setLoadingProcess(false);
      setLoadingResult(false);
      setStatus("error");
      setMessage(
        error?.message || "Ocurrió un error al generar el diccionario vehicular."
      );
    }
  };

  const handleConnectMercadoLibre = () => {
    if (checkingConnection || mlVerified) return;
    window.location.href = `${API_BASE}/auth/login`;
  };

  const connectButtonText = checkingConnection
    ? "Verificando conexión..."
    : mlVerified
    ? "✅ Cuenta conectada"
    : "Conectar con MercadoLibre";

  const statusText = checkingConnection
    ? "Verificando conexión con Mercado Libre..."
    : mlVerified
    ? "Conectado exitosamente"
    : mlStatusMessage;

  const generateButtonText =
    loadingResult
      ? "Cargando resumen..."
      : loadingProcess
      ? "Generando..."
      : "Generar Diccionario Vehicular";

  return (
    <>
      <ProcessingOverlay
        visible={loadingProcess}
        progress={progress}
        message={processMessage}
      />

      <section className="compat-page">
        <div className="compat-upload-layout">
          <div className="ml-connection-block">
            <button
              className={`process-button-ml ${mlVerified ? "connected" : ""}`}
              onClick={handleConnectMercadoLibre}
              disabled={checkingConnection || mlVerified}
              type="button"
            >
              {connectButtonText}
            </button>

            <p className={`ml-status ${mlVerified ? "success" : "pending"}`}>
              {statusText}
            </p>
          </div>

          <div className="actions-row centered-action">
            <button
              className="process-button"
              onClick={handleGenerateDictionary}
              disabled={
                !mlVerified ||
                !mlUserId ||
                status === "processing" ||
                checkingConnection
              }
              type="button"
            >
              {generateButtonText}
            </button>
          </div>

          {message && !loadingProcess && (
            <p className={`status-message ${status}`}>{message}</p>
          )}

          {jobId && (
            <div className="job-debug-info">
              <p>Job: {jobId}</p>
            </div>
          )}
        </div>
      </section>

      <ResultModal
        open={showResultModal}
        onClose={handleCloseResultModal}
        summary={jobResult?.summary}
        results={jobResult?.results}
      />
    </>
  );
}

export default LoadVehicleDictionary;