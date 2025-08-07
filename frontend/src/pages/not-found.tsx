import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="text-center space-y-6">
      <h1 className="text-4xl font-bold text-gray-900">404</h1>
      <h2 className="text-2xl font-semibold text-gray-700">Page Not Found</h2>
      <p className="text-gray-600 max-w-md mx-auto">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button onClick={() => (window.location.href = "/")}>Go Home</Button>
    </div>
  );
}
