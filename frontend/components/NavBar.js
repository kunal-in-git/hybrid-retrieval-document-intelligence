"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import BackendStatus from "@/components/BackendStatus";
import styles from "./NavBar.module.css";

const LINKS = [
  { href: "/", label: "Ask" },
  { href: "/documents", label: "Documents" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        <span className={styles.brand}>Hybrid Retrieval</span>

        <div className={styles.links}>
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={
                pathname === link.href
                  ? `${styles.link} ${styles.active}`
                  : styles.link
              }
            >
              {link.label}
            </Link>
          ))}
        </div>

        <BackendStatus />
      </nav>
    </header>
  );
}
