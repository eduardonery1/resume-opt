
import Navbar from "./components/Navbar";
import Optimizer from "./pages/Optimizer";
import Home from "./pages/Home";
import { BrowserRouter, Route, Routes } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <div className="App">
          <Navbar/>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/optimizer" element={<Optimizer />} />
          </Routes>  
      </div>
    </BrowserRouter>
  );
}

export default App;
