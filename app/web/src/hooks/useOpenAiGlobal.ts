import { useEffect, useState } from "react";

type OpenAiGlobalKey = "toolOutput" | "widgetState";

declare global {
  interface Window {
    openai?: any;
  }
}

export function useOpenAiGlobal<T = any>(key: OpenAiGlobalKey): T | undefined {
  const [value, setValue] = useState<T | undefined>(() =>
    window.openai ? window.openai[key] : undefined
  );

  useEffect(() => {
    if (!window.openai || !window.openai.subscribeToGlobal) return;

    const unsubscribe = window.openai.subscribeToGlobal(
      key,
      (val: T | undefined) => {
        setValue(val);
      }
    );

    return () => {
      unsubscribe?.();
    };
  }, [key]);

  return value;
}
