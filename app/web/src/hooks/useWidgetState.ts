import { useEffect, useState } from "react";

declare global {
  interface Window {
    openai?: any;
  }
}

export function useWidgetState<TState = any>(
  getDefaultState?: () => TState
): [TState | undefined, (next: TState | ((prev?: TState) => TState)) => void] {
  const [state, setState] = useState<TState | undefined>(() => {
    if (!window.openai) return getDefaultState?.();
    return window.openai.widgetState ?? getDefaultState?.();
  });

  useEffect(() => {
    if (!window.openai || !window.openai.subscribeToGlobal) return;

    const unsubscribe = window.openai.subscribeToGlobal(
      "widgetState",
      (newState: TState | undefined) => {
        setState(newState);
      }
    );

    return () => {
      unsubscribe?.();
    };
  }, []);

  const updateState = (next: TState | ((prev?: TState) => TState)) => {
    setState((prev) => {
      const resolved =
        typeof next === "function"
          ? (next as (p?: TState) => TState)(prev)
          : next;

      if (window.openai?.setWidgetState) {
        window.openai.setWidgetState(resolved);
      }

      return resolved;
    });
  };

  return [state, updateState];
}
