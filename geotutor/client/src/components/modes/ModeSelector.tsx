import { MODES, getMode, type ModeId } from "./registry";

// Segmented control shown at the left of the composer. It is live while the
// composer is empty; once a thread has started the mode is fixed for that
// thread and this renders as a read-only badge instead.

export function ModeSelector({
  value,
  onChange,
  locked = false,
}: {
  value: ModeId;
  onChange: (id: ModeId) => void;
  locked?: boolean;
}) {
  if (locked) {
    const mode = getMode(value);
    const Icon = mode.icon;
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${mode.tag}`}
        title={`This conversation is in ${mode.fullName} mode. Start a new task to change mode.`}
      >
        <Icon className="w-3.5 h-3.5" />
        {mode.fullName}
      </span>
    );
  }

  return (
    <div className="inline-flex items-center rounded-full bg-muted p-0.5" role="tablist">
      {MODES.map((mode) => {
        const Icon = mode.icon;
        const active = mode.id === value;
        return (
          <button
            key={mode.id}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={!mode.enabled}
            onClick={() => mode.enabled && onChange(mode.id)}
            title={mode.enabled ? mode.description : `${mode.fullName}: coming soon`}
            className={[
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
              active
                ? "bg-background text-foreground shadow-sm"
                : mode.enabled
                  ? "text-muted-foreground hover:text-foreground"
                  : "text-muted-foreground/40 cursor-not-allowed",
            ].join(" ")}
          >
            <Icon className="w-3.5 h-3.5" />
            {mode.label}
            {!mode.enabled && (
              <span className="text-[9px] uppercase tracking-wide opacity-70">soon</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
