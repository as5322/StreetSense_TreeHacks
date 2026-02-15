type Props = {
  showHeatmap: boolean;
  toggle: () => void;
};

export default function HeatmapToggle({ showHeatmap, toggle }: Props) {
  return (
    <button
      onClick={toggle}
      style={{
        position: "absolute",
        top: 20,
        right: 20,
        zIndex: 1,
        padding: "10px 16px",
        backgroundColor: showHeatmap ? "#FF3B30" : "#007AFF",
        color: "white",
        border: "none",
        borderRadius: "8px",
        cursor: "pointer",
        fontWeight: "bold",
      }}
    >
      {showHeatmap ? "Hide Heatmap" : "Show Heatmap"}
    </button>
  );
}
