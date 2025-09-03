import PageHeader from "@/components/PageHeader";

export default function LiveView() {
  return (
    <div className="mx-auto flex h-full min-h-0 max-w-6xl flex-col overflow-hidden px-6">
      <PageHeader title="Live View" description="Monitor your getgather operations in real-time" />
      <div className="min-h-0 flex-1 overflow-hidden">
        <div className="relative mx-auto aspect-video w-full max-w-[1920px]">
          <iframe
            src="http://localhost:23456/live/"
            className="absolute inset-0 h-full w-full border-0"
          />
        </div>
      </div>
    </div>
  );
}
