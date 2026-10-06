import { Children, useEffect, useRef } from "react";

const VISIBLE_APPOINTMENTS = 3;

export default function AppointmentList({ children, label }) {
  const listRef = useRef(null);
  const scrollable = Children.count(children) > VISIBLE_APPOINTMENTS;

  useEffect(() => {
    const list = listRef.current;
    if (!scrollable) return;

    const visibleCards = Array.from(list.children).slice(0, VISIBLE_APPOINTMENTS);
    const updateHeight = () => {
      const gap = parseFloat(getComputedStyle(list).rowGap) || 0;
      const height = visibleCards.reduce(
        (total, card) => total + card.getBoundingClientRect().height,
        gap * (visibleCards.length - 1)
      );
      list.style.maxHeight = `${height}px`;
    };
    const observer = new ResizeObserver(updateHeight);
    visibleCards.forEach((card) => observer.observe(card));
    updateHeight();
    return () => {
      observer.disconnect();
      list.style.removeProperty("max-height");
    };
  }, [children, scrollable]);

  return (
    <ul
      ref={listRef}
      className="appointmentsList scrollableAppointmentsList"
      tabIndex={scrollable ? 0 : undefined}
      aria-label={label}
    >
      {children}
    </ul>
  );
}
