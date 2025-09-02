import PageHeader from "@/components/PageHeader";

export default function LiveView() {
  return (
    <div className="max-w-6xl mx-auto px-6 h-full flex flex-col min-h-0 overflow-hidden">
      <PageHeader
        title="Live View"
        description="Monitor your getgather operations in real-time"
      />
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="relative w-full max-w-[1920px] mx-auto aspect-video">
          <iframe
            src="http://localhost:23456/live/"
            className="absolute inset-0 h-full w-full border-0"
          />
        </div>
      </div>
    </div>
  );
}
