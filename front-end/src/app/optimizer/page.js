"use client"

import { useState } from "react";
import Stepper from "../components/stepper";

export default function Optimizer() {
  const [currStep, setCurrStep] = useState(0);
  const steps = ["Resume and Job info", "Template Selection", "Download file"];

  return (
    <main className="flex flex-col items-center h-full justify-start">
      <Stepper currStep={currStep} steps={steps} />
      <div className="w-3/5 min-h-[60vh] shadow-[4px_4px_20px_0px_var(--shadow)]"></div>
      <div className="flex justify-between items-center m-4 h-12 w-3/5 gap-12">
        <button className={(currStep > 0) ? "border-none h-full text-xl font-semibold text-[var(--background)] bg-[var(--stepper-curr)] flex-[0.5_0_1]" : "border-none h-full text-xl font-semibold bg-[var(--stepper)] flex-[0.5_0_1] text-[var(--background)]"} onClick={() => {
          setCurrStep(prevState => {
            return (prevState > 0) ? prevState - 1 : 0;
          })
        }}>
          Back
        </button>

        <button className={(currStep < steps.length - 1) ? "border-none h-full text-xl font-semibold text-[var(--background)] bg-[var(--stepper-curr)] flex-[0.5_0_1]" : "border-none h-full text-xl font-semibold bg-[var(--stepper)] flex-[0.5_0_1] text-[var(--background)]"} onClick={() => {
          setCurrStep(prevState => {
            return (prevState < steps.length - 1) ? prevState + 1 : steps.length - 1;
          })
        }}>
          Next
        </button>
      </div>
    </main>
  )
}