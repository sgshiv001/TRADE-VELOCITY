import { useEffect, useRef } from "react";

export const tutorialSteps = [
  {
    page: "dashboard", title: "Read your order book",
    text: "The overview shows resting buy and sell orders, the best bid and ask, and the last match. Hosted traders see the same simulated order book.",
  },
  {
    page: "orders", title: "Try a partial fill",
    text: "In Orders & depth, choose a fresh practice symbol. Place a limit sell for 5 shares at ₹100, then place a limit buy for 3 at ₹101 on the same symbol. The engine matches 3 at ₹100 and leaves 2 shares open. You can place the buy from a second account.",
  },
  {
    page: "history", title: "Review the execution",
    text: "Trade history shows the fill price and quantity. Use Orders & depth to amend or cancel the remaining order. Your workspace is saved between visits.",
  },
] as const;

export const fundedTutorialSteps = [
  {page: "funded", title: "Start with your demo demat account",
    text: "Your account starts with ₹10 lakh in virtual cash. Choose a supported NSE stock to see its latest available provider price and the simulated order book."},
  {page: "funded", title: "Place a demo buy or sell",
    text: "Once bids and asks appear, enter a quantity and try a market or limit buy. After a fill adds shares to your holdings, you can sell them. A limit order with no match can stay open."},
  {page: "portfolio", title: "Check your holdings",
    text: "Portfolio shows your positions, virtual cash, and profit or loss. The order journal records fills and any quantity still open."},
] as const;

export default function Tutorial({step, steps, onStep, onDismiss}: {
  step: number; steps: readonly {title: string; text: string}[];
  onStep: (step: number) => void; onDismiss: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const current = steps[step];
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
      <p className="fine-print">Step {step + 1} of {steps.length}</p>
      <h2 id="tutorial-title">{current.title}</h2>
      <p>{current.text}</p>
    </div>
    <div className="tutorial-actions">
      {step > 0 && <button className="secondary-button" onClick={() => onStep(step - 1)}>Back</button>}
      {step === 1 && <button className="secondary-button" onClick={onDismiss}>Try placing an order</button>}
      {step < steps.length - 1
        ? <button className="primary-button" onClick={() => onStep(step + 1)}>Next</button>
        : <button className="primary-button" onClick={onDismiss}>Finish tutorial</button>}
    </div>
  </dialog>;
}
