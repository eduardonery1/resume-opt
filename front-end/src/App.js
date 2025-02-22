
import Navbar from "./components/Navbar";
import Optimizer from "./pages/Optimizer";
import Home from "./pages/Home";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Contact from "./pages/Contact";
import About from "./pages/About";

import "./styles/App.css"

function App() {
  return (
    <BrowserRouter>
      <div className="App">
          <Navbar/>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/optimizer" element={<Optimizer />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>  
      </div>
    </BrowserRouter>
  );
}

export default App;
