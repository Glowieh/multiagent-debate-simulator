type TopicFormProps = {
  onSubmit: (topic: string) => void;
  onAbort: () => void;
  onClear: () => void;
  isStreaming: boolean;
  hasDebateContent: boolean;
};

export function TopicForm({
  onSubmit,
  onAbort,
  onClear,
  isStreaming,
  hasDebateContent,
}: TopicFormProps) {
  return (
    <form
      className="topic-form"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const input = form.elements.namedItem("topic") as HTMLInputElement;
        const topic = input.value.trim();
        if (topic) onSubmit(topic);
      }}
    >
      <label htmlFor="topic">Debate topic</label>
      <div className="topic-form-row">
        <input
          id="topic"
          name="topic"
          type="text"
          placeholder="e.g. Should AI replace human teachers?"
          disabled={isStreaming}
          required
        />
        <button type="submit" disabled={isStreaming}>
          Start debate
        </button>
        <button
          type="button"
          className="btn-abort"
          disabled={!isStreaming}
          onClick={onAbort}
        >
          Abort
        </button>
        <button
          type="button"
          className="btn-clear"
          disabled={isStreaming || !hasDebateContent}
          onClick={onClear}
        >
          Clear debate
        </button>
      </div>
    </form>
  );
}
