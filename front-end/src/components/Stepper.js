import "./Stepper.css"

export default function Stepper({currStep, steps}){

    const stepDivs = steps.map((stepText, index) => {
        return (
            <div className="step" key={index}><div className={`stepNumber ${( index === currStep) ? "currStepNumber" : ""}`}>{index+1}</div><div className={`stepText ${( index === currStep) ? "currStepText" : ""}`}>{stepText}</div></div>
        )
    });


    
    return (
        <div className="stepper">
            {stepDivs}
        </div>
    )
}