import { useEffect, useRef } from "react";

export const tutorialSteps = [
  {
    page: "dashboard", title: "Read your order book",
    text: "The overview shows resting buy and sell orders, the best bid and ask, and the last match. Your practice workspace starts empty.",
  },
  {
    page: "orders", title: "Try a partial fill",
    text: "In Orders & depth, submit a limit sell for 5 shares at ₹100, then a limit buy for 3 shares at ₹101 on the same symbol. The engine matches 3 shares at the resting price of ₹100 and leaves 2 shares open.",
  },
  {
    page: "history", title: "Review the execution",
    text: "Trade history shows the fill price and quantity. Use Orders & depth to amend or cancel the remaining order. Your workspace is saved between visits.",
  },
] as const;

export default function Tutorial({step, onStep, onDismiss}: {
  step: number; onStep: (step: number) => void; onDismiss: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const current = tutorialSteps[step];
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);

  return <dialog className="panel tutorial-dialog" ref={dialog} aria-labelledby="tutorial-title"
    onCancel={event => { event.preventDefault(); onDismiss(); }}>
    <div className="tutorial-top">
      <span className="eyebrow">Workspace tutorial</span>
      <button className="text-button" onClick={onDismiss}>Skip tutorial</button>
    </div>
    <div aria-live="polite">
      <p className="fine-print">Step {step + 1} of {tutorialSteps.length}</p>
      <h2 id="tutorial-title">{current.title}</h2>
      <p>{current.text}</p>
    </div>
    <div className="tutorial-actions">
      {step > 0 && <button className="secondary-button" onClick={() => onStep(step - 1)}>Back</button>}
      {step === 1 && <button className="secondary-button" onClick={onDismiss}>Try placing an order</button>}
      {step < tutorialSteps.length - 1
        ? <button className="primary-button" onClick={() => onStep(step + 1)}>Next</button>
        : <button className="primary-button" onClick={onDismiss}>Finish tutorial</button>}
    </div>
  </dialog>;
}
