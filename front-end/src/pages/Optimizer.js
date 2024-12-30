import React, { useState } from "react"
import Stepper from "../components/Stepper"
import "../styles/Optimizer.css"


export default function Optimizer(){

    const [currStep, setCurrStep] = useState(0);
    const steps = ["Resume and Job info", "Template Selection", "Download file"]

    return (
        <main className="optimizerMain">
            <Stepper currStep={currStep} steps={steps}/>
            <div className="stepPanel"></div>
            <div className="buttonsContainer">
                <button className={(currStep > 0) ? "activeButton": "desactiveButton"} onClick={()=>{setCurrStep(prevState =>{
                    return (prevState > 0) ? prevState-1 : 0; 
                })}}>Back</button>
                <button className={(currStep < steps.length-1) ? "activeButton": "desactiveButton"} onClick={()=>{setCurrStep(prevState=>{
                    return (prevState < steps.length-1) ? prevState+1 : steps.length-1;
                })}}>Next</button></div>
        </main>

    )
}