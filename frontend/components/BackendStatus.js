"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

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

  if (status === "checking") {
    return <p>Checking backend...</p>;
  }

  if (status === "ok") {
    return <p>Backend: connected</p>;
  }

  return <p>Backend: not reachable</p>;
}
