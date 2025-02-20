import "./Stepper.css"

export default function Stepper({currStep, steps}){

    const stepDivs = steps.map((stepText, index, stepsArray) => {
        return (
            <>
                <div className="step" key={index}><div className={`stepNumber ${( index <= currStep) ? "currStepNumber" : ""}`}>{index+1}</div><div className={`stepText ${( index <= currStep) ? "currStepText" : ""}`}>{stepText}</div></div>
                {index < (stepsArray.length-1) && <div className={`stepSpacer ${(index < currStep) ? "stepSpacerDone": ""}` }></div>}
            </>
        )
    });

    
    
    return (
        <div className="stepper">
            {stepDivs}
        </div>
    )
}