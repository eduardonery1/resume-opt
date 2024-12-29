import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom"
import "./Navbar.css"

export default function Navbar(){
    return (
        <nav className="navbar">
            <div className="navlogo"></div>
            <div className="navlinks">
                <NavLink to="/" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Home</NavLink>
                <NavLink to="/optimizer" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Optimizer</NavLink>
                <NavLink to="/about" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>About Us</NavLink>
                <NavLink to="/contact" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Contact</NavLink>
            </div>
            <div className="navmenu"></div>

        </nav>        
    )
}