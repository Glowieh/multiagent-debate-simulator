import { useFollowScroll } from "../hooks/useFollowScroll";
import type { DisplayItem } from "../utils/debateEvents";
import {
  isWaitingForTurnText,
  partitionDisplayItems,
  toolCallLabel,
  turnLabel,
} from "../utils/debateEvents";

type DebateViewProps = {
  items: DisplayItem[];
  isStreaming: boolean;
};

type DebaterColumnProps = {
  side: "red" | "green";
  label: string;
  items: DisplayItem[];
  isWaitingForText: boolean;
};

function TurnLoadingIndicator() {
  return (
    <p className="turn-loading" aria-live="polite" aria-label="Waiting for response">
      <span className="turn-loading-dot" />
      <span className="turn-loading-dot" />
      <span className="turn-loading-dot" />
    </p>
  );
}

function ColumnItem({ item }: { item: DisplayItem }) {
  if (item.kind === "message") {
    return <p className="debate-message">{item.content}</p>;
  }

  const turn = turnLabel(item.event);
  if (turn) {
    return <p className="turn-marker">{turn}</p>;
  }

  const toolLabel = toolCallLabel(item.event);
  if (toolLabel) {
    return <p className="tool-call-message">{toolLabel}</p>;
  }

  return null;
}

function DebaterColumn({
  side,
  label,
  items,
  isWaitingForText,
}: DebaterColumnProps) {
  return (
    <section className={`debate-column debater-${side}`}>
      <h2 className="debate-column-heading">{label}</h2>
      <div className="debate-column-content">
        {items.length === 0 ? (
          <p className="debate-column-empty">Waiting for arguments…</p>
        ) : (
          items.map((item) => <ColumnItem key={item.key} item={item} />)
        )}
        {isWaitingForText && <TurnLoadingIndicator />}
      </div>
    </section>
  );
}

export function DebateView({ items, isStreaming }: DebateViewProps) {
  const containerRef = useFollowScroll(items.length);

  if (items.length === 0 && !isStreaming) {
    return <p className="empty-state">Submit a topic to start the debate.</p>;
  }

  const { redItems, greenItems, summaryContent } = partitionDisplayItems(items);

  return (
    <div className="debate-view" ref={containerRef}>
      <div className="debate-columns">
        <DebaterColumn
          side="red"
          label="Red"
          items={redItems}
          isWaitingForText={isStreaming && isWaitingForTurnText(redItems)}
        />
        <DebaterColumn
          side="green"
          label="Green"
          items={greenItems}
          isWaitingForText={isStreaming && isWaitingForTurnText(greenItems)}
        />
      </div>
      {summaryContent && (
        <section className="debate-summary">
          <h2 className="debate-summary-heading">Summary</h2>
          <p className="debate-summary-content">{summaryContent}</p>
        </section>
      )}
    </div>
  );
}
