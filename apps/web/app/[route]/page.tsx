import Client from "../Client";

export function generateStaticParams() {
  return ["app", "login", "signup", "desktop-sign-in"].map(route => ({route}));
}

export default function Page() {
  return <Client />;
}
