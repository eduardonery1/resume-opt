import React, { useState } from "react"
import Stepper from "../components/Stepper"

export default function Optimizer(){

    const [currStep, setCurrStep] = useState(0);

    return (
        <main>
            <Stepper currStep={currStep} steps={["Resume and Job info", "Template Selection", "Download file"]}/>

        </main>

    )
}