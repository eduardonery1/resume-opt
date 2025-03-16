'use client';

import { useState } from 'react';

export default function JobsResumeInfo({ uploadedFile, setUploadedFile}) {
  const [jobLinks, setJobLinks] = useState(['', '', '']);
  const [dragActive, setDragActive] = useState(false);

  const handleJobChange = (index, value) => {
    const updatedLinks = [...jobLinks];
    updatedLinks[index] = value;
    setJobLinks(updatedLinks);
  };

  const addJobField = () => setJobLinks([...jobLinks, '']);

  const removeJobField = (index) => {
    setJobLinks(jobLinks.filter((_, i) => i !== index));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
    }
  };

  return (
      <div className="shadow-md rounded-lg p-6 w-full lg:max-w-6xl sm:max-w-4xl grid grid-cols-2 gap-6 relative">
        <div>
          <h2 className="text-center font-semibold text-lg mb-4 text-[var(--stepper-curr)]">Jobs</h2>
          <div className="space-y-3">
            {jobLinks.map((link, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Paste job link"
                  value={link}
                  onChange={(e) => handleJobChange(index, e.target.value)}
                  className="w-full p-2 border rounded-lg bg-[var(--stepper)] placeholder-[var(--background)] focus:outline-none focus:ring-2 focus:ring-[var(--stepper-curr)]"
                />
                <button onClick={() => removeJobField(index)} className="w-8 h-8 bg-[var(--stepper)] flex items-center justify-center rounded-full shadow-md hover:bg-[var(--stepper-curr)] transition text-[var(--background)] ">
                  -
                </button>
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-4">
            <button onClick={addJobField} className="w-10 h-10 bg-[var(--stepper)] flex items-center justify-center rounded-full shadow-md hover:bg-[var(--stepper-curr)] transition text-[var(--background)]">
              +
            </button>
          </div>
        </div>

        <div className="absolute inset-y-0 left-1/2 w-0.5 bg-[var(--stepper-curr)]"></div>

        <div className="space-y-4">
          <h2 className="text-center font-semibold text-lg mb-4 text-[var(--stepper-curr)]">Resume</h2>
          <div
            className={`text-[var(--background)] w-full h-40 flex items-center justify-center border-2 border-dashed rounded-lg ${dragActive ? 'border-[var(--stepper-curr1)] bg-[var(--stepper1)]' : 'border-[var(--stepper-curr)] bg-[var(--stepper)]'}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {uploadedFile ? uploadedFile.name : 'drag the PDF file here'}
          </div>
          <input type="file" accept="application/pdf" id="fileUpload" onChange={handleFileUpload} className="hidden" />
          <label htmlFor="fileUpload" className="block w-full text-center bg-[var(--stepper)] p-2 rounded-lg cursor-pointer hover:bg-[var(--stepper-curr)] transition text-[var(--background)]">
            Select file
          </label>
        </div>
      </div>
  );
}
