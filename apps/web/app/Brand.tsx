export function Brand({href = "/"}: {href?: string}) {
  return <a className="tv2-brand" href={href} aria-label="TradeVelocity home">
    <img src="/tv-mark.svg" alt="" width={32} height={32} />
    <span>Trade<span>Velocity</span></span>
  </a>;
}
