import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom"
import "./Navbar.css"
import logo from "../assets/logo.png"
import menuIcon from "../assets/menu-icon.svg"

export default function Navbar(){
    return (
        <nav className="navbar">
            <div className="navlogo"><img src={logo} style={{height:"100%"}}/></div>
            <div className="navlinks">
                <NavLink to="/" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Home</NavLink>
                <NavLink to="/optimizer" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Optimizer</NavLink>
                <NavLink to="/about" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>About Us</NavLink>
                <NavLink to="/contact" className={({ isActive }) => isActive ? "currentLink" : "navlink"}>Contact</NavLink>
            </div>
            <button className="navmenu"><img src={menuIcon} style={{height:"100%"}}/></button>

        </nav>        
    )
}