type UploadedEvidencePanelProps = {
  title: string;
  text: string;
  status: string;
  locale: "zh" | "en";
  onTitleChange: (value: string) => void;
  onTextChange: (value: string) => void;
  onUpload: () => void;
};

export function UploadedEvidencePanel({
  title,
  text,
  status,
  locale,
  onTitleChange,
  onTextChange,
  onUpload,
}: UploadedEvidencePanelProps) {
  const hasText = Boolean(text.trim());

  return (
    <div className="compact-item" data-testid="upload-evidence-panel">
      <div className="compact-label">
        {locale === "en" ? "Uploaded evidence" : "\u4e0a\u4f20\u8bc1\u636e"}
      </div>
      <input
        value={title}
        onChange={(event) => onTitleChange(event.target.value)}
        placeholder={locale === "en" ? "Source title" : "\u6765\u6e90\u6807\u9898"}
        className="analyst-input"
      />
      <textarea
        value={text}
        onChange={(event) => onTextChange(event.target.value)}
        placeholder={
          locale === "en"
            ? "Paste a short note, CSV excerpt, ticket, or source snippet."
            : "\u7c98\u8d34\u77ed\u7b14\u8bb0\u3001CSV \u6458\u8981\u3001\u5de5\u5355\u6216\u6765\u6e90\u7247\u6bb5\u3002"
        }
        className="analyst-textarea"
        style={{
          marginTop: "7px",
          width: "100%",
          minHeight: "74px",
          resize: "vertical",
          border: "1px solid var(--analyst-border)",
          borderRadius: "8px",
          padding: "8px",
          background: "rgba(255,255,255,0.70)",
          color: "var(--analyst-ink)",
          fontSize: "0.64rem",
          lineHeight: 1.45,
        }}
      />
      <button
        type="button"
        onClick={onUpload}
        disabled={!hasText}
        style={{
          marginTop: "7px",
          width: "100%",
          padding: "8px 10px",
          borderRadius: "8px",
          border: "1px solid rgba(49, 95, 131, 0.24)",
          background: "rgba(255,255,255,0.66)",
          color: "#315f83",
          cursor: hasText ? "pointer" : "not-allowed",
          fontSize: "0.58rem",
          fontWeight: 800,
        }}
      >
        {locale === "en" ? "Store evidence" : "\u4fdd\u5b58\u8bc1\u636e"}
      </button>
      {status && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "0.54rem",
            color: "#7a6b55",
            lineHeight: 1.4,
          }}
        >
          {status}
        </div>
      )}
    </div>
  );
}
