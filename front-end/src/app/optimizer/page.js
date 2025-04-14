"use client";

import { useState } from "react";
import Stepper from "../components/stepper";
import JobsResumeInfo from "../components/jobs_resume_info";

const get_url_token = async () => {
  try {
    const response = await fetch(process.env.NEXT_PUBLIC_API_GET_AUTH, { method: "GET" });

    if (!response.ok) {
      console.error("Erro ao obter o token:", response.status);
      return null;
    }

    const data = await response.json();
    const token = data.auth;

    if (token) {
      console.log("Token obtained successfully");
      const request = `${process.env.NEXT_PUBLIC_API_POST_RESUME}?token=${token}`;
      return request;
    } else {
      console.error("Token obtain failed");
      return null;
    }
  } catch (error) {
    console.error("Error obtaining token:", error);
    return null;
  }
}

export default function Optimizer() {
  const [currStep, setCurrStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const steps = ["Resume and Job info", "Template Selection", "Download file"];

  const handleNext = async () => {
    if (currStep < steps.length - 1) {
      if (uploadedFile.type === "application/pdf") {
        const formData = new FormData();
        formData.append("resume", uploadedFile);

        const request = process.env.NODE_ENV == "development" ? 
          process.env.NEXT_PUBLIC_API_POST_RESUME_DEV_TOKEN : await get_url_token();

        console.log(request);
        try {
          const response = await fetch(request, {
            method: "POST",
            body: formData,
          });

          if (response.ok) {
            console.log("File uploaded successfully");
          } else {
            console.error("File upload failed");
          }
        } catch(error) {
          console.error("Error uploading file:", error);
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