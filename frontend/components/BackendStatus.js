"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import styles from "./BackendStatus.module.css";

const LABELS = {
  checking: "Checking backend",
  ok: "Backend online",
  down: "Backend offline",
};

export default function BackendStatus() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    async function check() {
      try {
        await getHealth();
        setStatus("ok");
      } catch {
        setStatus("down");
      }
    }

    check();
  }, []);

  return (
    <span className={`${styles.status} ${styles[status]}`}>
      <span className={styles.dot} />
      {LABELS[status]}
    </span>
  );
}
