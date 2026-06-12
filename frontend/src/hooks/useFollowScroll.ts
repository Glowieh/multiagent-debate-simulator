import { useCallback, useEffect, useRef } from "react";

const BOTTOM_THRESHOLD_PX = 80;

function isNearBottom(): boolean {
  return (
    window.innerHeight + window.scrollY >=
    document.documentElement.scrollHeight - BOTTOM_THRESHOLD_PX
  );
}

/**
 * Keeps the viewport pinned to the bottom while content grows, until the user
 * scrolls up. Scrolling back to the bottom re-enables follow mode.
 */
export function useFollowScroll(itemsLength: number) {
  const containerRef = useRef<HTMLDivElement>(null);
  const followingRef = useRef(true);

  const scrollToBottom = useCallback(() => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: "auto",
    });
  }, []);

  useEffect(() => {
    if (itemsLength === 0) {
      followingRef.current = true;
    }
  }, [itemsLength]);

  useEffect(() => {
    const onScroll = () => {
      followingRef.current = isNearBottom();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const observer = new ResizeObserver(() => {
      if (followingRef.current) {
        scrollToBottom();
      }
    });
    observer.observe(container);

    return () => observer.disconnect();
  }, [scrollToBottom]);

  return containerRef;
}
