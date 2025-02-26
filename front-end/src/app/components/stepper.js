export default function Stepper({ currStep, steps }) {

  const stepDivs = steps.map((stepText, index, stepsArray) => {
    return (
      <div className="flex items-center gap-2" key={index}>
        <div className={`h-8 flex justify-center items-center font-black aspect-square bg-[var(--stepper)] text-[var(--background)] rounded-full ${(index <= currStep) ? "text-[var(--background) bg-[var(--stepper-curr)]" : ""}`}>
          {index + 1}
        </div>
        <div className={`text-2xl font-semibold text-[var(--stepper)] ${(index <= currStep) ? "text-[var(--stepper-curr)]" : ""}`}>
          {stepText}
        </div>

        {index < (stepsArray.length - 1) && (
          <div className={`h-1 flex-1 rounded-[100px] bg-[var(--stepper)]${(index < currStep) ? "bg-[var(--stepper-curr)]" : ""}`}></div>
        )}
      </div>
    )
  });

  return (
    <div className="w-4/5 h-32 flex justify-around items-center gap-4 p-8">
      {stepDivs}
    </div>
  )
}