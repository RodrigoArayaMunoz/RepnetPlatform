import { BrowserRouter, Route, Routes } from "react-router-dom";
import MainLayout from "../src/frontend/layouts/MainLayout";
import Home from "../src/frontend/pages/Home";
import Compatibilidades from "./frontend/pages/CompatibilitiesUpload";
import PreciosStock from "./frontend/pages/PriceStocksUploads";
import NoCompatibilidades from "./frontend/pages/NoCompatibilities";
import Diccionario from "./frontend/pages/LoadVehicleDictionary";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route
            path="/compatibilidades/carga-masiva"
            element={<Compatibilidades />}
          />
          <Route
            path="/compatibilidades/no-compatibilidades"
            element={<NoCompatibilidades />}
          />
          <Route
            path="/actualizaciones/precios-stock"
            element={<PreciosStock />}
          />
          <Route
            path="/diccionario/cargar-diccionario"
            element={<Diccionario />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}