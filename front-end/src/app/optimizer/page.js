"use client";

import { useState } from "react";
import Stepper from "../components/stepper";
import JobsResumeInfo from "../components/jobs_resume_info";

export default function Optimizer() {
  const [currStep, setCurrStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const steps = ["Resume and Job info", "Template Selection", "Download file"];

  const handleNext = async () => {
    if (currStep < steps.length - 1) {
      if (uploadedFile) {
        const formData = new FormData();
        formData.append('resume', uploadedFile);

        try {
          const response = await fetch('https://clever-kindness-copy-production.up.railway.app/resume?token=nery', {
            method: 'POST',
            body: formData,
          });

          if (response.ok) {
            console.log('File uploaded successfully');
          } else {
            console.error('File upload failed');
          }
        } catch (error) {
          console.error('Error uploading file:', error);
        }
      }

      setCurrStep(prevState => prevState + 1);
    }
  };

  return (
    <main className="flex flex-col items-center h-full justify-start">
      <Stepper currStep={currStep} steps={steps} />
      <JobsResumeInfo uploadedFile={uploadedFile} setUploadedFile={setUploadedFile}/>
      
      <div className="flex justify-between items-center m-4 h-12 w-3/5 gap-12">
        <button className={(currStep > 0) ? "border-none h-full w-1/2 text-xl font-semibold text-[var(--background)] bg-[var(--stepper-curr)] flex-[0.5_0_1]" : "border-none h-full w-1/2 text-xl font-semibold bg-[var(--stepper)] flex-[0.5_0_1] text-[var(--background)]"} onClick={() => {
          setCurrStep(prevState => {
            return (prevState > 0) ? prevState - 1 : 0;
          })
        }}>
          Back
        </button>

        <button className={(currStep < steps.length - 1) ? "border-none h-full w-1/2 text-xl font-semibold text-[var(--background)] bg-[var(--stepper-curr)] flex-[0.5_0_1]" : "border-none h-full w-1/2 text-xl font-semibold bg-[var(--stepper)] flex-[0.5_0_1] text-[var(--background)]"} onClick={handleNext}>
          Next
        </button>
      </div>
    </main>
  )
}