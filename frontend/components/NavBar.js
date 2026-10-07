import Link from "next/link";

export default function NavBar() {
  return (
    <nav>
      <Link href="/">Ask</Link> | <Link href="/documents">Documents</Link>
    </nav>
  );
}
