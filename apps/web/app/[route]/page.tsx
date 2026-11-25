import Client from "../Client";

export function generateStaticParams() {
  return ["app", "login", "signup"].map(route => ({route}));
}

export default function Page() {
  return <Client />;
}
